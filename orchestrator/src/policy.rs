//! Pure admission and termination decisions, independently testable.
pub const GIB: u64 = 1024 * 1024 * 1024;
pub fn reservation(source_pixels: u64, output_pixels: u64) -> u64 {
    2 * GIB + 128 * source_pixels + 1024 * output_pixels
}
pub fn maximum_jobs(cpus: usize) -> usize {
    (cpus / 4).clamp(1, 4)
}
pub fn threads(cpus: usize) -> usize {
    ((cpus * 8 / 10) / maximum_jobs(cpus)).max(1)
}
pub fn sequence(number: u64) -> String {
    assert!(number > 0);
    let mut group = (number - 1) / 999;
    let mut prefix = String::new();
    while group > 0 {
        group -= 1;
        prefix.insert(0, (b'a' + (group % 26) as u8) as char);
        group /= 26;
    }
    format!("{prefix}{:03}", (number - 1) % 999 + 1)
}
#[derive(Clone, Copy, Debug)]
pub struct Sample {
    pub total: u64,
    pub available: u64,
    pub cpu: f32,
    pub managed: u64,
}
impl Sample {
    pub fn valid(self) -> bool {
        self.total > 0
            && self.available <= self.total
            && self.cpu.is_finite()
            && (0.0..=100.0).contains(&self.cpu)
    }
    pub fn admit(self, required: u64, unused: u64, active: usize, cool_samples: usize) -> bool {
        self.valid()
            && self.cpu < 80.0
            && (active == 0 || cool_samples >= 2)
            && self
                .available
                .saturating_sub(unused)
                .saturating_sub(required)
                >= self.total / 4
            && self.managed.saturating_add(unused).saturating_add(required) <= self.total * 3 / 4
    }
    pub fn terminate(self, low_samples: usize) -> bool {
        !self.valid() || low_samples >= 2 || self.managed > self.total * 3 / 4
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn overflow_names() {
        assert_eq!(sequence(1), "001");
        assert_eq!(sequence(999), "999");
        assert_eq!(sequence(1000), "a001");
        assert_eq!(sequence(999 * 27), "z999");
        assert_eq!(sequence(999 * 27 + 1), "aa001");
    }
    #[test]
    fn resource_decisions() {
        let mut s = Sample {
            total: 32 * GIB,
            available: 25 * GIB,
            cpu: 20.0,
            managed: 0,
        };
        assert!(s.admit(4 * GIB, 0, 0, 0));
        assert!(!s.admit(4 * GIB, 0, 1, 1));
        assert!(s.admit(4 * GIB, 0, 1, 2));
        s.cpu = 80.0;
        assert!(!s.admit(4 * GIB, 0, 0, 2));
        assert!(!s.terminate(0));
        s.available = 6 * GIB;
        assert!(!s.admit(4 * GIB, 0, 0, 2));
        assert!(s.terminate(2));
        s.managed = 25 * GIB;
        assert!(s.terminate(0));
        s.total = 0;
        assert!(!s.valid());
    }
}

pub fn stage_limit(stage: &str) -> u64 {
    match stage {
        "initialization" | "prepare" | "browser_initialization" => 120,
        "browser_wait" => 300,
        _ => 60,
    }
}
pub fn expired(stage: &str, stage_seconds: u64, active_seconds: u64) -> bool {
    stage_seconds >= stage_limit(stage) || active_seconds >= 900
}
#[cfg(test)]
mod deadline_tests {
    use super::*;
    #[test]
    fn timeout_boundaries() {
        assert!(!expired("initialization", 119, 119));
        assert!(expired("initialization", 120, 120));
        assert!(expired("render", 60, 100));
        assert!(!expired("browser_wait", 299, 400));
        assert!(expired("browser_wait", 300, 400));
        assert!(expired("export", 1, 900));
    }
}
