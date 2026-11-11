use serde_json::{Value, json};
use std::{
    fs::{self, File, OpenOptions},
    io::{self, Write},
    path::{Path, PathBuf},
    time::{Duration, SystemTime},
};
/// Only typed, application-owned fields enter logs. Worker payloads are never copied.
pub struct Logger {
    dir: PathBuf,
    file: File,
    path: PathBuf,
    run: String,
    segment: u32,
    bytes: u64,
}
impl Logger {
    pub fn new(dir: &Path, run: &str) -> io::Result<Self> {
        fs::create_dir_all(dir)?;
        let path = dir.join(format!("{run}-000.jsonl"));
        let file = OpenOptions::new()
            .create_new(true)
            .write(true)
            .open(&path)?;
        let log = Self {
            dir: dir.into(),
            file,
            path,
            run: run.into(),
            segment: 0,
            bytes: 0,
        };
        log.prune()?;
        Ok(log)
    }
    fn prune(&self) -> io::Result<()> {
        let mut closed = Vec::new();
        for entry in fs::read_dir(&self.dir)? {
            let entry = entry?;
            let path = entry.path();
            if path == self.path || path.extension().and_then(|s| s.to_str()) != Some("jsonl") {
                continue;
            }
            let meta = entry.metadata()?;
            // Live runs keep a companion lock file. Never prune their segments.
            let name = entry.file_name().to_string_lossy().into_owned();
            let prefix = name.rsplit_once('-').map(|p| p.0).unwrap_or("");
            let marker = self.dir.join(format!("{prefix}.active"));
            if marker.exists() {
                let pid = fs::read_to_string(&marker)
                    .ok()
                    .and_then(|s| s.trim().parse::<i32>().ok());
                if pid.is_some_and(|pid| pid > 0 && unsafe { libc::kill(pid, 0) } == 0) {
                    continue;
                }
                fs::remove_file(marker)?;
            }
            let modified = meta.modified()?;
            if SystemTime::now()
                .duration_since(modified)
                .unwrap_or_default()
                > Duration::from_secs(30 * 86400)
            {
                fs::remove_file(path)?;
            } else {
                closed.push((modified, meta.len(), path));
            }
        }
        closed.sort_by_key(|r| r.0);
        let mut total: u64 = closed.iter().map(|r| r.1).sum();
        for (_, size, path) in closed {
            if total <= 250 * 1024 * 1024 {
                break;
            }
            fs::remove_file(path)?;
            total -= size;
        }
        Ok(())
    }
    pub fn event(&mut self, job: Option<&str>, event: &str, details: Value) -> io::Result<()> {
        let line = serde_json::to_vec(
            &json!({"time":chrono::Utc::now().to_rfc3339(),"run_id":self.run,"job_id":job,"event":event,"details":details}),
        )?;
        if self.bytes + line.len() as u64 > 10 * 1024 * 1024 {
            self.file.sync_all()?;
            self.segment += 1;
            self.path = self
                .dir
                .join(format!("{}-{:03}.jsonl", self.run, self.segment));
            self.file = OpenOptions::new()
                .create_new(true)
                .write(true)
                .open(&self.path)?;
            self.bytes = 0;
            self.prune()?;
        }
        self.file.write_all(&line)?;
        self.file.write_all(b"\n")?;
        self.file.flush()?;
        self.bytes += line.len() as u64 + 1;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn rotation_retention_and_live_segments() {
        let folder = tempfile::tempdir().unwrap();
        let old = folder.path().join("old-000.jsonl");
        let file = File::create(&old).unwrap();
        file.set_times(
            std::fs::FileTimes::new()
                .set_modified(SystemTime::now() - Duration::from_secs(31 * 86400)),
        )
        .unwrap();
        let live = folder.path().join("live-000.jsonl");
        let file = File::create(&live).unwrap();
        file.set_len(260 * 1024 * 1024).unwrap();
        fs::write(
            folder.path().join("live.active"),
            std::process::id().to_string(),
        )
        .unwrap();
        let mut logger = Logger::new(folder.path(), "run").unwrap();
        assert!(!old.exists());
        assert!(live.exists());
        logger.bytes = 10 * 1024 * 1024;
        logger
            .event(Some("job-001"), "stage", json!({"stage":"render"}))
            .unwrap();
        assert!(folder.path().join("run-001.jsonl").exists());
        let closed = folder.path().join("closed-000.jsonl");
        File::create(&closed)
            .unwrap()
            .set_len(251 * 1024 * 1024)
            .unwrap();
        logger.prune().unwrap();
        assert!(!closed.exists());
        assert!(live.exists());
    }
}
