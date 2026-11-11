use clap::{Args, Parser, Subcommand};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    collections::{HashSet, VecDeque},
    fs::{self, File, OpenOptions},
    io::{BufRead, BufReader, Read, Write},
    os::unix::{fs::PermissionsExt, io::AsRawFd, process::CommandExt},
    path::{Path, PathBuf},
    process::{Child, ChildStdin, Command, Stdio},
    sync::{
        Arc,
        atomic::{AtomicBool, Ordering},
        mpsc,
    },
    thread,
    time::{Duration, Instant},
};
use sysinfo::{Pid, ProcessesToUpdate, System};
use wall_e::{
    logging::Logger,
    policy::{self, Sample},
    state::{self, Job},
};
type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;
const WARNING: &str = "This aspect ratio may produce an awkward composition or an incomplete-looking background. The complete source photo will still be preserved.";

#[derive(Parser)]
#[command(version, about = "WALL-E — wallpaper engine made by DH-thejose")]
struct Cli {
    #[arg(long, global = true, default_value = ".")]
    workspace: PathBuf,
    #[command(subcommand)]
    command: Action,
}
#[derive(Subcommand)]
enum Action {
    Init,
    Doctor,
    Render(Render),
    Resume { jobs: Vec<String> },
}
#[derive(Args)]
struct Render {
    #[arg(required = true)]
    photos: Vec<PathBuf>,
    #[arg(long,conflicts_with_all=["width","height","reference"])]
    preset: Option<String>,
    #[arg(long, requires = "height", conflicts_with = "reference")]
    width: Option<u32>,
    #[arg(long, requires = "width", conflicts_with = "reference")]
    height: Option<u32>,
    #[arg(long)]
    reference: Option<PathBuf>,
    #[arg(long, requires = "preset")]
    swap: bool,
    #[arg(long, help = "Border percentage per edge, 3 through 20")]
    border: Option<f64>,
    #[arg(long)]
    brand: Option<String>,
}
#[derive(serde::Deserialize)]
#[serde(deny_unknown_fields)]
struct Settings {
    brand: String,
    width: u32,
    height: u32,
    border: f64,
}
struct Engine {
    python: PathBuf,
    source: Option<PathBuf>,
    browsers: PathBuf,
}
impl Engine {
    fn locate() -> Result<Self> {
        let exe = std::env::current_exe()?;
        let install = exe.parent().and_then(Path::parent).ok_or("installation")?;
        if install.join("env/bin/python").exists() {
            return Ok(Self {
                python: install.join("env/bin/python"),
                source: None,
                browsers: install.join("browsers"),
            });
        }
        let root = Path::new(env!("CARGO_MANIFEST_DIR")).parent().unwrap();
        Ok(Self {
            python: root.join(".venv/bin/python"),
            source: Some(root.join("Photo-to-Wallpaper-Rendering-Engine/src")),
            browsers: root
                .join("Photo-to-Wallpaper-Rendering-Engine/tool-package-shelf/browser-binaries"),
        })
    }
    fn command(&self) -> Command {
        let mut cmd = Command::new(&self.python);
        cmd.args(["-m", "wallpaper_engine.worker"])
            .env("PLAYWRIGHT_BROWSERS_PATH", &self.browsers)
            .env("PYTHONDONTWRITEBYTECODE", "1")
            .env("PYTHONUNBUFFERED", "1")
            .env_remove("PYTHONHOME")
            .env_remove("PYTHONPATH")
            .stderr(Stdio::null());
        if let Some(source) = &self.source {
            cmd.env("PYTHONPATH", source);
        }
        cmd.process_group(0);
        cmd
    }
    fn probe(&self, source: Option<&Path>, cancel: &AtomicBool) -> Result<Value> {
        let mut cmd = self.command();
        if let Some(source) = source {
            cmd.arg("--inspect").arg(source);
        } else {
            cmd.arg("--doctor");
        }
        cmd.stdout(Stdio::piped());
        let mut process = ManagedChild(cmd.spawn()?, false);
        let begin = Instant::now();
        loop {
            if cancel.load(Ordering::Relaxed) {
                return Err("cancelled".into());
            }
            if let Some(status) = process.0.try_wait()? {
                let mut output = String::new();
                process
                    .0
                    .stdout
                    .take()
                    .ok_or("protocol")?
                    .take(65537)
                    .read_to_string(&mut output)?;
                if !status.success() || output.len() > 65536 {
                    return Err("invalid_input_or_environment".into());
                }
                let result: Value = serde_json::from_str(output.trim()).map_err(|_| "protocol")?;
                if result["version"] != 1 {
                    return Err("protocol".into());
                }
                return Ok(result);
            }
            if begin.elapsed() > Duration::from_secs(120) {
                return Err("initialization_timeout".into());
            }
            thread::sleep(Duration::from_millis(30));
        }
    }
}
struct ManagedChild(Child, bool);
impl ManagedChild {
    fn stop(&mut self) {
        if self.1 {
            return;
        }
        self.1 = true;
        let pg = self.0.id() as i32;
        unsafe {
            libc::kill(-pg, libc::SIGTERM);
        }
        let until = Instant::now() + Duration::from_secs(2);
        loop {
            if unsafe { libc::kill(-pg, 0) } != 0 || Instant::now() >= until {
                break;
            }
            thread::sleep(Duration::from_millis(30));
        }
        unsafe {
            libc::kill(-pg, libc::SIGKILL);
        }
        let _ = self.0.wait();
    }
}
impl Drop for ManagedChild {
    fn drop(&mut self) {
        self.stop();
    }
}
struct WorkspaceLock(File);
impl WorkspaceLock {
    fn acquire(path: &Path) -> Result<Self> {
        let file = OpenOptions::new()
            .create(true)
            .truncate(false)
            .read(true)
            .write(true)
            .open(path)?;
        if unsafe { libc::flock(file.as_raw_fd(), libc::LOCK_EX | libc::LOCK_NB) } != 0 {
            return Err("workspace_busy".into());
        }
        Ok(Self(file))
    }
}
impl Drop for WorkspaceLock {
    fn drop(&mut self) {
        unsafe {
            libc::flock(self.0.as_raw_fd(), libc::LOCK_UN);
        }
    }
}
struct ActiveMarker(PathBuf);
impl Drop for ActiveMarker {
    fn drop(&mut self) {
        let _ = fs::remove_file(&self.0);
    }
}
fn initialize(workspace: &Path) -> Result<()> {
    fs::create_dir_all(workspace)?;
    for name in ["wall-pic-in", "wall-pic-out", "logs", ".wallpaper"] {
        let path = workspace.join(name);
        if path.is_symlink() {
            return Err("workspace_symlink".into());
        }
        fs::create_dir_all(&path)?;
        fs::set_permissions(&path, fs::Permissions::from_mode(0o700))?;
    }
    let settings = workspace.join(".wallpaper/settings.json");
    if !settings.exists() {
        let mut file = OpenOptions::new()
            .create_new(true)
            .write(true)
            .open(settings)?;
        file.write_all(b"{\"brand\":\"WALL-E\",\"width\":1920,\"height\":1080,\"border\":0.05}\n")?;
    }
    Ok(())
}
fn validate_target(w: u32, h: u32, border: f64) -> Result<bool> {
    if w.min(h) < 512 || w.max(h) > 8192 || w as u64 * h as u64 > 16_777_216 {
        return Err("target_size_limit".into());
    }
    if w * 3 < h || w > h * 3 {
        return Err("manual_layout_required".into());
    }
    if !border.is_finite() || !(0.03..=0.20).contains(&border) {
        return Err("border_range".into());
    }
    Ok(w * 2 < h || w > h * 2)
}
fn valid_brand(brand: &str) -> bool {
    !brand.is_empty()
        && brand.len() <= 48
        && brand
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_')
}
fn hash(path: &Path) -> Result<String> {
    let mut file = File::open(path)?;
    let mut h = Sha256::new();
    let mut buffer = [0; 65536];
    loop {
        let count = file.read(&mut buffer)?;
        if count == 0 {
            break;
        }
        h.update(&buffer[..count]);
    }
    Ok(format!("{:x}", h.finalize()))
}
fn tree_memory(system: &System, root: Pid) -> u64 {
    let mut pids = HashSet::from([root]);
    loop {
        let before = pids.len();
        for (pid, p) in system.processes() {
            if p.parent().is_some_and(|id| pids.contains(&id)) {
                pids.insert(*pid);
            }
        }
        if before == pids.len() {
            break;
        }
    }
    pids.iter()
        .filter_map(|pid| system.process(*pid))
        .map(|p| p.memory())
        .sum()
}
struct Worker {
    job: Job,
    child: ManagedChild,
    input: ChildStdin,
    events: mpsc::Receiver<Option<Value>>,
    work: PathBuf,
    started: Instant,
    stage_start: Instant,
    stage: String,
    waiting: bool,
    slot: bool,
    result: Option<Value>,
    failure: Option<(&'static str, bool)>,
    eof: bool,
    reservation: u64,
    memory: u64,
    peak: u64,
}
impl Worker {
    fn launch(
        engine: &Engine,
        mut job: Job,
        workspace: &Path,
        threads: usize,
        reservation: u64,
    ) -> Result<Self> {
        let date = workspace.join("wall-pic-out").join(&job.date);
        fs::create_dir_all(&date)?;
        if date.is_symlink() {
            return Err("output_symlink".into());
        }
        let work = date.join(format!(".{}.staging", job.id));
        if work.exists() {
            return Err("staging_collision".into());
        }
        fs::create_dir(&work)?;
        let mut child = ManagedChild(
            engine
                .command()
                .stdin(Stdio::piped())
                .stdout(Stdio::piped())
                .spawn()?,
            false,
        );
        let mut input = child.0.stdin.take().ok_or("worker_stdin")?;
        let request = json!({"version":1,"type":"job","source":job.source,"source_sha256":job.hash,"width":job.width,"height":job.height,"border":job.border,"styles":["blur","gallery","frosted","gradient"],"work_dir":work,"threads":threads});
        writeln!(input, "{request}")?;
        input.flush()?;
        let stdout = child.0.stdout.take().ok_or("worker_stdout")?;
        let (tx, rx) = mpsc::sync_channel(128);
        thread::spawn(move || {
            let mut reader = BufReader::new(stdout);
            loop {
                let mut bytes = Vec::new();
                match reader.by_ref().take(65537).read_until(b'\n', &mut bytes) {
                    Ok(0) => break,
                    Ok(_) if bytes.len() <= 65536 => {
                        let value = serde_json::from_slice(&bytes).unwrap_or(Value::Null);
                        if tx.send(Some(value)).is_err() {
                            return;
                        }
                    }
                    _ => {
                        let _ = tx.send(Some(Value::Null));
                        break;
                    }
                }
            }
            let _ = tx.send(None);
        });
        job.attempts += 1;
        job.status = "running".into();
        Ok(Self {
            job,
            child,
            input,
            events: rx,
            work,
            started: Instant::now(),
            stage_start: Instant::now(),
            stage: "initialization".into(),
            waiting: false,
            slot: false,
            result: None,
            failure: None,
            eof: false,
            reservation,
            memory: 0,
            peak: 0,
        })
    }
    fn receive(&mut self, log: &mut Logger) -> Result<()> {
        for _ in 0..64 {
            let Ok(message) = self.events.try_recv() else {
                break;
            };
            let Some(value) = message else {
                self.eof = true;
                break;
            };
            if value["version"] != 1 || self.result.is_some() || self.failure.is_some() {
                self.failure = Some(("protocol", false));
                break;
            }
            match value["type"].as_str() {
                Some("stage") => {
                    let stage = value["stage"].as_str().unwrap_or("");
                    if !["prepare", "browser_initialization", "render", "export"].contains(&stage) {
                        self.failure = Some(("protocol", false));
                        break;
                    }
                    let style = value["style"].as_str().unwrap_or("");
                    if stage != "prepare"
                        && !["blur", "gallery", "frosted", "gradient"].contains(&style)
                    {
                        self.failure = Some(("protocol", false));
                        break;
                    }
                    self.stage = stage.into();
                    self.stage_start = Instant::now();
                    log.event(
                        Some(&self.job.id),
                        "stage",
                        json!({"stage":stage,"style":style}),
                    )?;
                }
                Some("progress") => {}
                Some("browser_slot_request") if !self.waiting && !self.slot => {
                    self.waiting = true;
                    self.stage = "browser_wait".into();
                    self.stage_start = Instant::now();
                }
                Some("browser_slot_release") if self.slot => {
                    self.slot = false;
                }
                Some("complete") => {
                    self.result = Some(value);
                }
                Some("error") => {
                    let code = value["code"].as_str().unwrap_or("");
                    self.failure = Some(match code {
                        "browser_startup" => ("browser_startup", true),
                        "invalid_input" => (
                            match value["reason"].as_str() {
                                Some("invalid_profile") => "invalid_profile",
                                Some("untagged_cmyk") => "untagged_cmyk",
                                Some("multi_frame") => "multi_frame_input",
                                Some("decoded_pixels") => "input_pixel_limit",
                                _ => "invalid_input",
                            },
                            false,
                        ),
                        "verification_failed" => ("verification", false),
                        _ => ("processing_failed", false),
                    });
                }
                _ => {
                    self.failure = Some(("protocol", false));
                }
            }
        }
        Ok(())
    }
}
impl Drop for Worker {
    fn drop(&mut self) {
        self.child.stop();
        if self.work.exists() {
            let _ = fs::remove_dir_all(&self.work);
        }
    }
}
fn verify_result(job: &Job, result: &Value, dir: &Path, published: bool) -> Result<()> {
    if dir.is_symlink() {
        return Err("verification".into());
    }
    if result["version"] != 1
        || result["type"] != "complete"
        || result["source_sha256"] != job.hash
        || result["dimensions"] != json!([job.width, job.height])
    {
        return Err("verification".into());
    }
    let artifacts = result["artifacts"].as_array().ok_or("verification")?;
    if artifacts.len() != 4 {
        return Err("verification".into());
    }
    for (i, artifact) in artifacts.iter().enumerate() {
        let name = if published {
            format!("{}.{}.png", job.id, i + 1)
        } else {
            format!("{}.png", i + 1)
        };
        let path = dir.join(name);
        if path.is_symlink()
            || !path.is_file()
            || artifact["sha256"].as_str() != Some(hash(&path)?.as_str())
            || artifact["checks"]["foreground_exact"] != true
            || artifact["checks"]["crc_valid"] != true
            || artifact["checks"]["trailing_bytes"] != 0
        {
            return Err("verification".into());
        }
        if !published && artifact["path"].as_str() != path.to_str() {
            return Err("verification".into());
        }
    }
    Ok(())
}
fn publish(job: &Job, result: &Value, work: &Path, workspace: &Path) -> Result<()> {
    verify_result(job, result, work, false)?;
    // Prepared work and destination share a filesystem. RENAME_EXCL forbids replacing even an empty directory.
    for i in 1..=4 {
        let source = work.join(format!("{i}.png"));
        File::open(&source)?.sync_all()?;
        fs::rename(source, work.join(format!("{}.{i}.png", job.id)))?;
    }
    File::open(work)?.sync_all()?;
    let destination = workspace.join("wall-pic-out").join(&job.date).join(&job.id);
    #[cfg(target_os = "macos")]
    {
        use std::{ffi::CString, os::unix::ffi::OsStrExt};
        let from = CString::new(work.as_os_str().as_bytes())?;
        let to = CString::new(destination.as_os_str().as_bytes())?;
        if unsafe { libc::renamex_np(from.as_ptr(), to.as_ptr(), libc::RENAME_EXCL) } != 0 {
            return Err("output_collision_or_publication".into());
        }
    }
    #[cfg(not(target_os = "macos"))]
    return Err("unsupported_platform".into());
    File::open(destination.parent().unwrap())?.sync_all()?;
    Ok(())
}
fn schedule(
    engine: &Engine,
    workspace: &Path,
    db: &rusqlite::Connection,
    jobs: Vec<Job>,
    cancel: &AtomicBool,
    log: &mut Logger,
) -> Result<bool> {
    let mut queue: VecDeque<(Job, Instant)> =
        jobs.into_iter().map(|j| (j, Instant::now())).collect();
    let mut active: Vec<Worker> = Vec::new();
    let mut all_ok = true;
    let mut system = System::new_all();
    let cpus = system.cpus().len();
    let max_jobs = policy::maximum_jobs(cpus);
    let threads = policy::threads(cpus);
    let mut last_sample = Instant::now();
    let mut samples = 0;
    let mut cool = 0;
    let mut low = 0;
    let mut sample = Sample {
        total: 0,
        available: 0,
        cpu: 100.0,
        managed: 0,
    };
    let mut peak = state::peak(db);
    let mut cancelled = false;
    while !queue.is_empty() || !active.is_empty() {
        if cancel.load(Ordering::Relaxed) {
            cancelled = true;
        }
        if cancelled {
            for (mut job, _) in queue.drain(..) {
                job.status = "cancelled".into();
                state::save(db, &job)?;
                log.event(Some(&job.id), "cancelled", json!({}))?;
            }
            for worker in &mut active {
                worker.failure = Some(("cancelled", false));
            }
            all_ok = false;
        }
        for worker in &mut active {
            worker.receive(log)?;
        }
        if last_sample.elapsed() >= Duration::from_secs(1) {
            system.refresh_memory();
            system.refresh_cpu_usage();
            system.refresh_processes(ProcessesToUpdate::All, true);
            let own = system.process(Pid::from_u32(std::process::id()));
            let mut managed = own.map(|p| p.memory()).unwrap_or(0);
            let mut monitoring_failed = cpus == 0 || own.is_none() || managed == 0;
            for w in &mut active {
                w.memory = tree_memory(&system, Pid::from_u32(w.child.0.id()));
                w.peak = w.peak.max(w.memory);
                managed += w.memory;
                if w.memory == 0 && w.child.0.try_wait()?.is_none() {
                    monitoring_failed = true;
                }
            }
            sample = Sample {
                total: system.total_memory(),
                available: system.available_memory(),
                cpu: system.global_cpu_usage(),
                managed,
            };
            samples += 1;
            cool = if sample.cpu < 70.0 { cool + 1 } else { 0 };
            low = if sample.available < sample.total / 5 {
                low + 1
            } else {
                0
            };
            log.event(None,"resources",json!({"total_bytes":sample.total,"available_bytes":sample.available,"cpu_percent":sample.cpu,"managed_bytes":managed,"active_jobs":active.len()}))?;
            if monitoring_failed || !sample.valid() {
                for w in &mut active {
                    w.failure = Some(("monitoring_failed", false));
                }
                cancelled = true;
                all_ok = false;
                log.event(None, "monitoring_failed", json!({}))?;
            } else if sample.terminate(low)
                && let Some(w) = active.iter_mut().max_by_key(|w| w.memory)
            {
                w.failure = Some(("memory_limit", false));
            }
            last_sample = Instant::now();
        }
        let slot_busy = active.iter().any(|w| w.slot);
        if !slot_busy
            && !cancelled
            && let Some(w) = active.iter_mut().find(|w| w.waiting && w.failure.is_none())
        {
            writeln!(
                w.input,
                "{}",
                json!({"version":1,"type":"browser_slot_grant"})
            )?;
            w.input.flush()?;
            w.waiting = false;
            w.slot = true;
            w.stage = "browser_initialization".into();
            w.stage_start = Instant::now();
            log.event(Some(&w.job.id), "browser_grant", json!({}))?;
        }
        for w in &mut active {
            if policy::expired(
                &w.stage,
                w.stage_start.elapsed().as_secs(),
                w.started.elapsed().as_secs(),
            ) {
                w.failure = Some(("timeout", false));
            }
        }
        let mut index = 0;
        while index < active.len() {
            let exit = active[index].child.0.try_wait()?;
            if active[index].failure.is_none() && !(exit.is_some() && active[index].eof) {
                index += 1;
                continue;
            }
            let mut w = active.remove(index);
            if w.failure.is_none() && (exit.is_none_or(|s| !s.success()) || w.result.is_none()) {
                w.failure = Some(("worker_crash", true));
            }
            if w.failure.is_none() {
                let result = w.result.as_ref().unwrap();
                let checked = verify_result(&w.job, result, &w.work, false);
                if checked.is_err() {
                    w.failure = Some(("verification", false));
                } else {
                    db.execute(
                        "INSERT OR REPLACE INTO results VALUES (?1,?2)",
                        rusqlite::params![w.job.id, result.to_string()],
                    )?;
                    if publish(&w.job, result, &w.work, workspace).is_err() {
                        w.failure = Some(("publication", false));
                    } else {
                        w.job.status = "complete".into();
                        state::save(db, &w.job)?;
                        log.event(Some(&w.job.id),"published",json!({"width":w.job.width,"height":w.job.height,"seconds":w.started.elapsed().as_secs_f64(),"verified":true,"renderers":["S1","S1","D3","S2"]}))?;
                        println!("{}: complete", w.job.id);
                    }
                }
            }
            peak = peak.max(w.peak);
            state::record_peak(db, peak)?;
            let retry = w
                .failure
                .is_some_and(|(_, retry)| retry && w.job.attempts < 2)
                && !cancelled;
            if let Some((code, _)) = w.failure {
                log.event(
                    Some(&w.job.id),
                    "failed",
                    json!({"code":code,"retry":retry,"attempt":w.job.attempts}),
                )?;
                w.job.status = if retry { "queued".into() } else { code.into() };
                state::save(db, &w.job)?;
                if !retry {
                    all_ok = false;
                    println!("{}: {code}", w.job.id);
                }
            }
            let job = w.job.clone();
            let work = w.work.clone();
            drop(w);
            if work.exists() {
                fs::remove_dir_all(work)?;
            }
            if retry {
                queue.push_back((job, Instant::now()));
            }
        }
        if let Some((job, queued)) = queue.front() {
            let reserve =
                policy::reservation(job.source_pixels, job.width as u64 * job.height as u64)
                    .max(peak);
            let unused: u64 = active
                .iter()
                .map(|w| w.reservation.saturating_sub(w.memory))
                .sum();
            if !cancelled
                && samples >= 2
                && active.len() < max_jobs
                && sample.admit(reserve, unused, active.len(), cool)
            {
                // Refresh memory immediately before admission; CPU comes from the successive one-second samples.
                system.refresh_memory();
                sample.available = system.available_memory();
                sample.total = system.total_memory();
                if sample.admit(reserve, unused, active.len(), cool) {
                    let (mut job, _) = queue.pop_front().unwrap();
                    match Worker::launch(engine, job.clone(), workspace, threads, reserve) {
                        Ok(w) => {
                            state::save(db, &w.job)?;
                            log.event(Some(&w.job.id),"started",json!({"attempt":w.job.attempts,"threads":threads,"reservation_bytes":reserve,"width":w.job.width,"height":w.job.height}))?;
                            active.push(w);
                        }
                        Err(_) => {
                            job.status = "worker_start_failed".into();
                            state::save(db, &job)?;
                            all_ok = false;
                            log.event(
                                Some(&job.id),
                                "failed",
                                json!({"code":"worker_start_failed"}),
                            )?;
                            let work = workspace
                                .join("wall-pic-out")
                                .join(&job.date)
                                .join(format!(".{}.staging", job.id));
                            if work.exists() {
                                fs::remove_dir_all(work)?;
                            }
                        }
                    }
                }
            } else if queued.elapsed() > Duration::from_secs(300)
                || reserve > sample.total * 3 / 4 && samples >= 2
            {
                let (mut job, _) = queue.pop_front().unwrap();
                job.status = "resource_refused".into();
                state::save(db, &job)?;
                all_ok = false;
                log.event(Some(&job.id), "failed", json!({"code":"resource_refused"}))?;
                println!("{}: resource_refused", job.id);
            }
        }
        thread::sleep(Duration::from_millis(30));
    }
    Ok(all_ok)
}
fn execute(cli: Cli, cancel: &AtomicBool) -> Result<bool> {
    initialize(&cli.workspace)?;
    let workspace = cli.workspace.canonicalize()?;
    for name in [
        "state.sqlite",
        "state.sqlite-wal",
        "state.sqlite-shm",
        "run.lock",
    ] {
        if workspace.join(".wallpaper").join(name).is_symlink() {
            return Err("state_symlink".into());
        }
    }
    let _lock = WorkspaceLock::acquire(&workspace.join(".wallpaper/run.lock"))?;
    let mut db = state::open(&workspace.join(".wallpaper/state.sqlite"))?;
    db.execute_batch(
        "CREATE TABLE IF NOT EXISTS results(id TEXT PRIMARY KEY, record TEXT NOT NULL);",
    )?;
    let engine = Engine::locate()?;
    if matches!(cli.command, Action::Init) {
        println!("Workspace initialized.");
        return Ok(true);
    }
    if matches!(cli.command, Action::Doctor) {
        engine.probe(None, cancel)?;
        let mut system = System::new_all();
        thread::sleep(Duration::from_secs(1));
        system.refresh_all();
        if system.total_memory() == 0 || system.process(Pid::from_u32(std::process::id())).is_none()
        {
            return Err("monitoring_failed".into());
        }
        println!("Engine, browser assets, WebGL, SQLite and OS monitoring available.");
        return Ok(true);
    }
    let run = format!(
        "{}-{}",
        chrono::Utc::now().format("%Y%m%dT%H%M%S%fZ"),
        std::process::id()
    );
    let marker = workspace.join("logs").join(format!("{run}.active"));
    writeln!(File::create(&marker)?, "{}", std::process::id())?;
    let _marker = ActiveMarker(marker);
    let mut log = Logger::new(&workspace.join("logs"), &run)?;
    let mut jobs = Vec::new();
    let mut all_ok = true;
    match cli.command {
        Action::Render(args) => {
            let settings: Settings =
                serde_json::from_slice(&fs::read(workspace.join(".wallpaper/settings.json"))?)
                    .map_err(|_| "invalid_settings")?;
            let brand = args.brand.unwrap_or_else(|| settings.brand.clone());
            if !valid_brand(&brand) {
                return Err("brand_must_use_letters_digits_hyphen_underscore".into());
            }
            let border = args.border.map(|b| b / 100.0).unwrap_or(settings.border);
            let (mut width, mut height) = if let Some(preset) = args.preset {
                let presets: Value =
                    serde_json::from_str(include_str!("../../config/presets.json"))?;
                let values = presets.get(&preset).ok_or("unknown_preset")?;
                (
                    values[0].as_u64().unwrap() as u32,
                    values[1].as_u64().unwrap() as u32,
                )
            } else if let Some(reference) = args.reference {
                let info = engine.probe(
                    Some(&reference.canonicalize().map_err(|_| "invalid_reference")?),
                    cancel,
                )?;
                (
                    info["dimensions"][0].as_u64().ok_or("invalid_reference")? as u32,
                    info["dimensions"][1].as_u64().ok_or("invalid_reference")? as u32,
                )
            } else {
                (
                    args.width.unwrap_or(settings.width),
                    args.height.unwrap_or(settings.height),
                )
            };
            if args.swap {
                std::mem::swap(&mut width, &mut height);
            }
            if validate_target(width, height, border)? {
                eprintln!("{WARNING}");
                log.event(
                    None,
                    "ratio_warning",
                    json!({"width":width,"height":height}),
                )?;
            }
            for photo in args.photos {
                if cancel.load(Ordering::Relaxed) {
                    all_ok = false;
                    break;
                }
                let info = photo
                    .canonicalize()
                    .map_err(|_| "invalid_input".into())
                    .and_then(|path| engine.probe(Some(&path), cancel).map(|v| (path, v)));
                match info {
                    Ok((path, info)) => {
                        let date = chrono::Local::now().format("%Y%m%d").to_string();
                        let job = state::allocate(
                            &mut db,
                            &date,
                            &brand,
                            Job {
                                id: String::new(),
                                date: String::new(),
                                source: path.to_str().ok_or("input_path_encoding")?.into(),
                                hash: info["sha256"].as_str().ok_or("protocol")?.into(),
                                width,
                                height,
                                border,
                                source_pixels: info["dimensions"][0].as_u64().ok_or("protocol")?
                                    * info["dimensions"][1].as_u64().ok_or("protocol")?,
                                status: "queued".into(),
                                attempts: 0,
                            },
                        )?;
                        log.event(
                            Some(&job.id),
                            "allocated",
                            json!({"width":width,"height":height}),
                        )?;
                        jobs.push(job);
                    }
                    Err(_) => {
                        all_ok = false;
                        log.event(None, "input_rejected", json!({"code":"invalid_input"}))?;
                        eprintln!("An input was rejected; continuing valid jobs.");
                    }
                }
            }
        }
        Action::Resume { jobs: ids } => {
            if ids.is_empty() {
                return Err("resume_requires_job_ids".into());
            }
            let mut unique = HashSet::new();
            for id in ids {
                if !unique.insert(id.clone()) {
                    continue;
                }
                let mut job = state::get(&db, &id).map_err(|_| "unknown_job")?;
                if job.date.len() != 8
                    || !job.date.bytes().all(|b| b.is_ascii_digit())
                    || job.id.len() > 100
                    || !job
                        .id
                        .bytes()
                        .all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-')
                {
                    return Err("invalid_job_state".into());
                }
                if workspace.join("wall-pic-out").join(&job.date).is_symlink() {
                    return Err("output_symlink".into());
                }
                validate_target(job.width, job.height, job.border)?;
                if hash(Path::new(&job.source)).ok().as_deref() != Some(job.hash.as_str()) {
                    log.event(
                        Some(&job.id),
                        "resume_rejected",
                        json!({"code":"input_changed"}),
                    )?;
                    all_ok = false;
                    continue;
                }
                let destination = workspace.join("wall-pic-out").join(&job.date).join(&job.id);
                if destination.exists() {
                    let record: std::result::Result<String, _> =
                        db.query_row("SELECT record FROM results WHERE id=?1", [&job.id], |r| {
                            r.get(0)
                        });
                    if let Ok(record) = record
                        && let Ok(result) = serde_json::from_str(&record)
                        && verify_result(&job, &result, &destination, true).is_ok()
                    {
                        job.status = "complete".into();
                        state::save(&db, &job)?;
                        println!("{}: already complete", job.id);
                        continue;
                    }
                    all_ok = false;
                    log.event(
                        Some(&job.id),
                        "resume_rejected",
                        json!({"code":"output_collision"}),
                    )?;
                    continue;
                }
                let work = destination
                    .parent()
                    .unwrap()
                    .join(format!(".{}.staging", job.id));
                if work.is_symlink() {
                    return Err("staging_symlink".into());
                }
                if work.exists() {
                    fs::remove_dir_all(work)?;
                }
                job.status = "queued".into();
                job.attempts = 0;
                state::save(&db, &job)?;
                jobs.push(job);
            }
        }
        _ => unreachable!(),
    }
    Ok(schedule(&engine, &workspace, &db, jobs, cancel, &mut log)? && all_ok)
}
fn main() {
    // Private state and runtime files should never inherit a permissive caller umask.
    unsafe {
        libc::umask(0o077);
    }
    let cli = Cli::parse();
    let cancel = Arc::new(AtomicBool::new(false));
    let signal = cancel.clone();
    if ctrlc::set_handler(move || {
        signal.store(true, Ordering::Relaxed);
    })
    .is_err()
    {
        eprintln!("WALL-E: signal_handler_failed");
        std::process::exit(3)
    }
    let code = match execute(cli, &cancel) {
        Ok(true) => 0,
        Ok(false) => 3,
        Err(error) => {
            let message = error.to_string();
            let safe = if message.bytes().all(|b| b.is_ascii_lowercase() || b == b'_') {
                message.as_str()
            } else {
                "operation_failed"
            };
            eprintln!("WALL-E: {safe}");
            if [
                "target_size_limit",
                "invalid_settings",
                "manual_layout_required",
                "border_range",
                "unknown_preset",
                "invalid_reference",
                "resume_requires_job_ids",
                "brand_must_use_letters_digits_hyphen_underscore",
            ]
            .contains(&safe)
            {
                2
            } else {
                3
            }
        }
    };
    std::process::exit(code)
}

#[cfg(test)]
mod tests {
    use super::*;
    fn fixture(script: &str) -> (tempfile::TempDir, Engine, rusqlite::Connection, Job, Logger) {
        let folder = tempfile::tempdir().unwrap();
        initialize(folder.path()).unwrap();
        let executable = folder.path().join("fake-worker");
        let python = Path::new(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .unwrap()
            .join(".venv/bin/python");
        fs::write(
            &executable,
            format!(
                "#!{}\nimport sys,json,os,time\njob=json.loads(sys.stdin.readline())\n{script}\n",
                python.display()
            ),
        )
        .unwrap();
        fs::set_permissions(&executable, fs::Permissions::from_mode(0o700)).unwrap();
        let mut db = state::open(&folder.path().join(".wallpaper/state.sqlite")).unwrap();
        db.execute_batch("CREATE TABLE results(id TEXT PRIMARY KEY, record TEXT NOT NULL);")
            .unwrap();
        let job = state::allocate(
            &mut db,
            "20261111",
            "TEST",
            Job {
                id: String::new(),
                date: String::new(),
                source: "private-path".into(),
                hash: "abc".into(),
                width: 512,
                height: 512,
                border: 0.05,
                source_pixels: 100,
                status: "queued".into(),
                attempts: 0,
            },
        )
        .unwrap();
        let log = Logger::new(&folder.path().join("logs"), "test-run").unwrap();
        let engine = Engine {
            python: executable,
            source: None,
            browsers: folder.path().join("browsers"),
        };
        (folder, engine, db, job, log)
    }
    #[test]
    fn target_policy_and_brand() {
        for (w, h, warn) in [
            (512, 1024, false),
            (1024, 512, false),
            (512, 1536, true),
            (1536, 512, true),
        ] {
            assert_eq!(validate_target(w, h, 0.05).unwrap(), warn);
        }
        assert!(validate_target(512, 1537, 0.05).is_err());
        assert!(validate_target(8192, 8192, 0.05).is_err());
        assert!(!valid_brand("../escape"));
        assert!(valid_brand("WALL-E"));
    }
    #[test]
    fn malformed_worker_is_terminal_and_cleaned() {
        let (folder, engine, db, job, mut log) =
            fixture("print(json.dumps({'version':9,'type':'stage'}),flush=True)\ntime.sleep(10)");
        let mut worker = Worker::launch(&engine, job, folder.path(), 1, policy::GIB).unwrap();
        let until = Instant::now() + Duration::from_secs(3);
        while worker.failure.is_none() && Instant::now() < until {
            thread::sleep(Duration::from_millis(20));
            worker.receive(&mut log).unwrap();
        }
        assert_eq!(worker.failure, Some(("protocol", false)));
        let work = worker.work.clone();
        drop(worker);
        assert!(!work.exists());
        drop(db);
    }
    #[test]
    #[ignore = "requires unrestricted OS process monitoring"]
    fn crash_retries_once_and_startup_retries_once() {
        for script in [
            "os._exit(42)",
            "print(json.dumps({'version':1,'type':'error','code':'browser_startup','retryable':True}),flush=True)\nsys.exit(3)",
        ] {
            let (folder, engine, db, job, mut log) = fixture(script);
            let id = job.id.clone();
            assert!(
                !schedule(
                    &engine,
                    folder.path(),
                    &db,
                    vec![job],
                    &AtomicBool::new(false),
                    &mut log
                )
                .unwrap()
            );
            let saved = state::get(&db, &id).unwrap();
            assert_eq!(saved.attempts, 2);
            assert!(matches!(
                saved.status.as_str(),
                "worker_crash" | "browser_startup"
            ));
            assert!(
                !folder
                    .path()
                    .join("wall-pic-out/20261111")
                    .join(format!(".{id}.staging"))
                    .exists()
            );
        }
    }
    #[test]
    #[ignore = "requires unrestricted OS process monitoring"]
    fn browser_contention_serializes_and_invalid_input_never_retries() {
        let script = r#"
print(json.dumps({'version':1,'type':'browser_slot_request'}),flush=True)
assert json.loads(sys.stdin.readline())=={'version':1,'type':'browser_slot_grant'}
lock=os.path.join(os.path.dirname(os.path.dirname(job['work_dir'])),'browser.lock')
try: os.mkdir(lock)
except FileExistsError:
    open(lock+'.collision','w').close()
    raise
# Keep the slot long enough for the second job to be admitted.
time.sleep(2)
os.rmdir(lock)
print(json.dumps({'version':1,'type':'browser_slot_release'}),flush=True)
print(json.dumps({'version':1,'type':'error','code':'invalid_input','retryable':False}),flush=True)
sys.exit(2)
"#;
        let (folder, engine, mut db, job, mut log) = fixture(script);
        let second = state::allocate(&mut db, "20261111", "TEST", job.clone()).unwrap();
        let ids = [job.id.clone(), second.id.clone()];
        assert!(
            !schedule(
                &engine,
                folder.path(),
                &db,
                vec![job, second],
                &AtomicBool::new(false),
                &mut log
            )
            .unwrap()
        );
        for id in ids {
            let saved = state::get(&db, &id).unwrap();
            assert_eq!(saved.attempts, 1);
            assert_eq!(saved.status, "invalid_input");
        }
        assert!(
            !folder
                .path()
                .join("wall-pic-out/browser.lock.collision")
                .exists()
        );
    }
    #[test]
    fn publication_does_not_replace_existing_directory() {
        let (folder, _engine, _db, job, _log) = fixture("pass");
        let work = folder.path().join("staging");
        fs::create_dir(&work).unwrap();
        let artifacts:Vec<_>=(1..=4).map(|i|{let p=work.join(format!("{i}.png"));fs::write(&p,b"synthetic").unwrap();json!({"path":p,"sha256":hash(&p).unwrap(),"checks":{"foreground_exact":true,"crc_valid":true,"trailing_bytes":0}})}).collect();
        let result = json!({"version":1,"type":"complete","source_sha256":job.hash,"dimensions":[512,512],"artifacts":artifacts});
        let destination = folder
            .path()
            .join("wall-pic-out")
            .join(&job.date)
            .join(&job.id);
        fs::create_dir_all(&destination).unwrap();
        fs::write(destination.join("keep"), b"unchanged").unwrap();
        assert!(publish(&job, &result, &work, folder.path()).is_err());
        assert_eq!(fs::read(destination.join("keep")).unwrap(), b"unchanged");
    }
}
