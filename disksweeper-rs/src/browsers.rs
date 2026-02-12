use std::path::PathBuf;

fn get_local_appdata() -> PathBuf {
    dirs::data_local_dir().unwrap_or_else(|| {
        let home = dirs::home_dir().unwrap_or_default();
        home.join("AppData").join("Local")
    })
}

fn iter_profile_caches(base: PathBuf) -> Vec<PathBuf> {
    let mut caches = Vec::new();

    if !base.exists() {
        return caches;
    }

    let entries = match std::fs::read_dir(&base) {
        Ok(e) => e,
        Err(_) => return caches,
    };

    for entry in entries.flatten() {
        let path = entry.path();
        if !path.is_dir() {
            continue;
        }

        // Check for Cache and Code Cache directories
        for cache_name in &["Cache", "Code Cache"] {
            let cache_dir = path.join(cache_name);
            if cache_dir.exists() {
                caches.push(cache_dir);
            }
        }
    }

    caches
}

/// Discover all Edge browser cache directories across profiles
pub fn edge_caches() -> Vec<PathBuf> {
    let base = get_local_appdata()
        .join("Microsoft")
        .join("Edge")
        .join("User Data");
    iter_profile_caches(base)
}

/// Discover all Chrome browser cache directories across profiles
pub fn chrome_caches() -> Vec<PathBuf> {
    let base = get_local_appdata()
        .join("Google")
        .join("Chrome")
        .join("User Data");
    iter_profile_caches(base)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_edge_caches_no_panic() {
        // Should not panic even if Edge is not installed
        let _ = edge_caches();
    }

    #[test]
    fn test_chrome_caches_no_panic() {
        // Should not panic even if Chrome is not installed
        let _ = chrome_caches();
    }
}
