use rusqlite::{Connection, TransactionBehavior, params};
use serde::{Deserialize, Serialize};
use std::path::Path;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Job {
    pub id: String,
    pub date: String,
    pub source: String,
    pub hash: String,
    pub width: u32,
    pub height: u32,
    pub border: f64,
    pub source_pixels: u64,
    pub status: String,
    pub attempts: u32,
}
pub fn open(path: &Path) -> Result<Connection, rusqlite::Error> {
    let db = Connection::open(path)?;
    db.busy_timeout(std::time::Duration::from_secs(30))?;
    db.execute_batch(
        "PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL;
        CREATE TABLE IF NOT EXISTS counters(date TEXT PRIMARY KEY, number INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, record TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS metrics(key TEXT PRIMARY KEY, value INTEGER NOT NULL);",
    )?;
    Ok(db)
}
pub fn allocate(
    db: &mut Connection,
    date: &str,
    brand: &str,
    mut job: Job,
) -> Result<Job, rusqlite::Error> {
    let tx = db.transaction_with_behavior(TransactionBehavior::Immediate)?;
    tx.execute(
        "INSERT INTO counters VALUES (?1,1) ON CONFLICT(date) DO UPDATE SET number=number+1",
        [date],
    )?;
    let number: u64 = tx.query_row("SELECT number FROM counters WHERE date=?1", [date], |r| {
        r.get(0)
    })?;
    job.id = format!("{brand}_{date}_{}", crate::policy::sequence(number));
    job.date = date.to_owned();
    tx.execute(
        "INSERT INTO jobs VALUES (?1,?2)",
        params![job.id, serde_json::to_string(&job).unwrap()],
    )?;
    tx.commit()?;
    Ok(job)
}
pub fn save(db: &Connection, job: &Job) -> Result<(), rusqlite::Error> {
    db.execute(
        "UPDATE jobs SET record=?2 WHERE id=?1",
        params![job.id, serde_json::to_string(job).unwrap()],
    )?;
    Ok(())
}
pub fn get(db: &Connection, id: &str) -> Result<Job, Box<dyn std::error::Error>> {
    let record: String = db.query_row("SELECT record FROM jobs WHERE id=?1", [id], |r| r.get(0))?;
    Ok(serde_json::from_str(&record)?)
}
pub fn peak(db: &Connection) -> u64 {
    db.query_row("SELECT value FROM metrics WHERE key='peak'", [], |r| {
        r.get(0)
    })
    .unwrap_or(0)
}
pub fn record_peak(db: &Connection, value: u64) -> Result<(), rusqlite::Error> {
    db.execute("INSERT INTO metrics VALUES ('peak',?1) ON CONFLICT(key) DO UPDATE SET value=MAX(value,excluded.value)",[value])?;
    Ok(())
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn concurrent_allocation_and_resume() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("state.sqlite");
        open(&path).unwrap();
        let handles: Vec<_> = (0..12)
            .map(|_| {
                let path = path.clone();
                std::thread::spawn(move || {
                    let mut db = open(&path).unwrap();
                    let job = allocate(
                        &mut db,
                        "20261111",
                        "WALL-E",
                        Job {
                            id: String::new(),
                            date: String::new(),
                            source: "private".into(),
                            hash: "abc".into(),
                            width: 1920,
                            height: 1080,
                            border: 0.05,
                            source_pixels: 10,
                            status: "queued".into(),
                            attempts: 0,
                        },
                    )
                    .unwrap();
                    assert_eq!(get(&db, &job.id).unwrap().hash, "abc");
                    job.id
                })
            })
            .collect();
        let ids: std::collections::HashSet<_> =
            handles.into_iter().map(|h| h.join().unwrap()).collect();
        assert_eq!(ids.len(), 12);
    }
}
