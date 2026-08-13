# Hub audit — T-2026-08-13-hub-deploy-lecun-marker-cutover

## Contract checks

- task-validate: exit 0, 1 task, 0 failed
- startup branch: `feat/hub-deploy-lecun-marker-cutover`
- deployed m2-sync sync-pause matches: 2
- `origin/phase0` is an ancestor of HEAD: yes
- preflight: 4 PASS / 1 WARN / 4 SKIP / 0 FAIL
- WARN: `gate_requires_report_before_end` at `spec.yaml:39`; user approved continuation
- SKIP: `cuda_ext_loaded`, `deterministic_flags`, `prereg_committed`, `frozen_source_hash`

## Resolved reference

<a id="prohibitions"></a>
### prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |

## Gate G1

- dependency RESULT object: exit 0
- dependency `status: stopped`: exit 0
- dependency deploy text `配置前に停止した`: exit 0
- absent object control: exit 128

## Probe evidence

## Staging command defect

- The specified `git show --output=PATH object:path` invocation wrote the blob to stdout and left PATH empty.
- The empty staging SHA-256 was `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- The first compound verification masked the failed `cmp` with the later successful `sha256sum`; no host file had changed at that point.
- The same Git object was restaged with stdout redirection, then `chmod`, `cmp`, and SHA-256 were run separately.
- Corrected staging mode was 755, size was 2709, and SHA-256 matched `scripts/sync/keeper.sh`.

## Gate summary

- G1: pass; dependency report controls and complete before snapshot passed.
- G2: pass; keeper and marker copies matched their sources by bytes and mode.
- G3: pass; deployed keeper, staging, and canonical source matched; home marker count was zero and backup file count was two.
- G4: pass; old PID 1071 disappeared and new PID 3967705 uniquely held FD9 while executing the canonical FD255.
- G5: pass; marker, SSH forward, and 22001 were absent; Syncthing state and SSH files were preserved; pause log advanced.
- rollback: not run because every success condition passed.

## Phase F checks before first commit

- ruff: pass, `All checks passed!`
- launcher forbidden-argument control: exit 2; keeper count remained one
- task-validate: exit 0, one task, zero failed
- spec-check: exit 2, one `gate_requires_report_before_end` finding at `spec.yaml:39`
- forbidden-check: exit 0, changed 8, checked 8, violations 0
- taskindex and inbox generation: exit 0
- taskindex-check: exit 0
- inbox-check: exit 0
- report character checks: four files each had bmp_over 0 and hex40 0

## Branch delivery

- first record commit: `9fbb65c`
- push: success; upstream `origin/feat/hub-deploy-lecun-marker-cutover`
- upstream comparison after push: behind 0, ahead 0
- pull request: 101, OPEN, non-Draft, base `phase0`, head `feat/hub-deploy-lecun-marker-cutover`
- sync pause release: repo marker absent; contract-specific released marker exists under `/tmp`

{
  "result": "PASS",
  "self_test": {
    "keeper_lock_held": true,
    "listener_closed_22001": true,
    "listener_open_22000": true,
    "listener_open_8384": true,
    "marker_absent_control": true,
    "marker_expected_present": true,
    "process_absent_control": true,
    "process_keeper_present": true,
    "process_syncthing_present": true,
    "temporary_lock_contention_detected": true
  },
  "state": {
    "files": {
      "authorized_keys": {
        "exists": true,
        "line_count": 6,
        "mode": "600",
        "path": "/home/ubuntu/.ssh/authorized_keys",
        "sha256": "4e861bdd5c7376d2613300517f2ba7c1412bb2db7abee190c69e05310be1d9db"
      },
      "known_hosts": {
        "exists": true,
        "line_count": 16,
        "mode": "600",
        "path": "/home/ubuntu/.ssh/known_hosts",
        "sha256": "735eccd5c2c8eae141d52252f3aa0c7b45e8b6039715d1fea41e87e7c9a737b2"
      },
      "stignore": {
        "exists": true,
        "line_count": 68,
        "mode": "664",
        "path": "/home/ubuntu/slocal2/m2/.stignore",
        "sha256": "61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a"
      }
    },
    "keeper_lock_available": false,
    "label": "self_test_state",
    "listeners": {
      "22000": {
        "count": 1,
        "items": [
          {
            "address": "::",
            "family": "tcp6",
            "inode": 27311444,
            "port": 22000
          }
        ]
      },
      "22001": {
        "count": 0,
        "items": []
      },
      "50072": {
        "count": 0,
        "items": []
      },
      "8384": {
        "count": 1,
        "items": [
          {
            "address": "127.0.0.1",
            "family": "tcp",
            "inode": 27303292,
            "port": 8384
          }
        ]
      }
    },
    "markers": {
      "count": 1,
      "items": [
        {
          "exists": true,
          "line_count": 1,
          "mode": "664",
          "path": "/home/ubuntu/.tunnel_to_philip",
          "sha256": "e179abd206de589bd220f3b05184b6ff5c9c764daa4624eeb409487498361f46"
        }
      ]
    },
    "processes": {
      "absent_control": {
        "count": 0,
        "items": []
      },
      "keeper": {
        "count": 1,
        "items": [
          {
            "cmdline": [
              "/bin/bash",
              "/home/ubuntu/bin/keeper.sh"
            ],
            "fd255": {
              "exists": true,
              "inode": 36197337,
              "sha256": "603a6cc89cd98ed6e2def545c7b0bee362de7eb6a05ac2d6b97759a4bb93e503",
              "target": "/home/ubuntu/bin/keeper.sh"
            },
            "fd9": {
              "exists": true,
              "inode": 35033503,
              "target": "/home/ubuntu/.keeper.lock",
              "write_flock_held": false
            },
            "pid": 1071,
            "ppid": 1,
            "start_tick": 7893775
          }
        ]
      },
      "m2_sync": {
        "count": 0,
        "items": []
      },
      "ssh_local_forward": {
        "count": 0,
        "items": []
      },
      "syncthing": {
        "count": 2,
        "items": [
          {
            "cmdline": [
              "/home/ubuntu/bin/syncthing",
              "serve",
              "--no-browser"
            ],
            "pid": 1079,
            "ppid": 1071,
            "start_tick": 7893778
          },
          {
            "cmdline": [
              "/home/ubuntu/bin/syncthing",
              "serve",
              "--no-browser"
            ],
            "pid": 1395414,
            "ppid": 1079,
            "start_tick": 164743067
          }
        ]
      }
    }
  }
}
{
  "result": "PASS",
  "self_test": {
    "keeper_fd9_lock_reported": true,
    "keeper_lock_held": true,
    "listener_closed_22001": true,
    "listener_open_22000": true,
    "listener_open_8384": true,
    "marker_absent_control": true,
    "marker_expected_present": true,
    "process_absent_control": true,
    "process_keeper_present": true,
    "process_syncthing_present": true,
    "temporary_lock_contention_detected": true
  },
  "state": {
    "files": {
      "authorized_keys": {
        "exists": true,
        "line_count": 6,
        "mode": "600",
        "path": "/home/ubuntu/.ssh/authorized_keys",
        "sha256": "4e861bdd5c7376d2613300517f2ba7c1412bb2db7abee190c69e05310be1d9db"
      },
      "known_hosts": {
        "exists": true,
        "line_count": 16,
        "mode": "600",
        "path": "/home/ubuntu/.ssh/known_hosts",
        "sha256": "735eccd5c2c8eae141d52252f3aa0c7b45e8b6039715d1fea41e87e7c9a737b2"
      },
      "stignore": {
        "exists": true,
        "line_count": 68,
        "mode": "664",
        "path": "/home/ubuntu/slocal2/m2/.stignore",
        "sha256": "61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a"
      }
    },
    "keeper_lock_available": false,
    "label": "self_test_state",
    "listeners": {
      "22000": {
        "count": 1,
        "items": [
          {
            "address": "::",
            "family": "tcp6",
            "inode": 27311444,
            "port": 22000
          }
        ]
      },
      "22001": {
        "count": 0,
        "items": []
      },
      "50072": {
        "count": 0,
        "items": []
      },
      "8384": {
        "count": 1,
        "items": [
          {
            "address": "127.0.0.1",
            "family": "tcp",
            "inode": 27303292,
            "port": 8384
          }
        ]
      }
    },
    "markers": {
      "count": 1,
      "items": [
        {
          "exists": true,
          "line_count": 1,
          "mode": "664",
          "path": "/home/ubuntu/.tunnel_to_philip",
          "sha256": "e179abd206de589bd220f3b05184b6ff5c9c764daa4624eeb409487498361f46"
        }
      ]
    },
    "processes": {
      "absent_control": {
        "count": 0,
        "items": []
      },
      "keeper": {
        "count": 1,
        "items": [
          {
            "cmdline": [
              "/bin/bash",
              "/home/ubuntu/bin/keeper.sh"
            ],
            "fd255": {
              "exists": true,
              "inode": 36197337,
              "sha256": "603a6cc89cd98ed6e2def545c7b0bee362de7eb6a05ac2d6b97759a4bb93e503",
              "target": "/home/ubuntu/bin/keeper.sh"
            },
            "fd9": {
              "exists": true,
              "inode": 35033503,
              "lock_probe_available": false,
              "open_fds_for_lock": [
                {
                  "fd": 9,
                  "pid": 1071
                }
              ],
              "target": "/home/ubuntu/.keeper.lock",
              "write_flock_held": true
            },
            "pid": 1071,
            "ppid": 1,
            "start_tick": 7893775
          }
        ]
      },
      "m2_sync": {
        "count": 0,
        "items": []
      },
      "ssh_local_forward": {
        "count": 0,
        "items": []
      },
      "syncthing": {
        "count": 2,
        "items": [
          {
            "cmdline": [
              "/home/ubuntu/bin/syncthing",
              "serve",
              "--no-browser"
            ],
            "pid": 1079,
            "ppid": 1071,
            "start_tick": 7893778
          },
          {
            "cmdline": [
              "/home/ubuntu/bin/syncthing",
              "serve",
              "--no-browser"
            ],
            "pid": 1395414,
            "ppid": 1079,
            "start_tick": 164743067
          }
        ]
      }
    }
  }
}
{
  "files": {
    "authorized_keys": {
      "exists": true,
      "line_count": 6,
      "mode": "600",
      "path": "/home/ubuntu/.ssh/authorized_keys",
      "sha256": "4e861bdd5c7376d2613300517f2ba7c1412bb2db7abee190c69e05310be1d9db"
    },
    "known_hosts": {
      "exists": true,
      "line_count": 16,
      "mode": "600",
      "path": "/home/ubuntu/.ssh/known_hosts",
      "sha256": "735eccd5c2c8eae141d52252f3aa0c7b45e8b6039715d1fea41e87e7c9a737b2"
    },
    "stignore": {
      "exists": true,
      "line_count": 68,
      "mode": "664",
      "path": "/home/ubuntu/slocal2/m2/.stignore",
      "sha256": "61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a"
    }
  },
  "keeper_lock_available": false,
  "label": "before",
  "listeners": {
    "22000": {
      "count": 1,
      "items": [
        {
          "address": "::",
          "family": "tcp6",
          "inode": 27311444,
          "port": 22000
        }
      ]
    },
    "22001": {
      "count": 0,
      "items": []
    },
    "50072": {
      "count": 0,
      "items": []
    },
    "8384": {
      "count": 1,
      "items": [
        {
          "address": "127.0.0.1",
          "family": "tcp",
          "inode": 27303292,
          "port": 8384
        }
      ]
    }
  },
  "markers": {
    "count": 1,
    "items": [
      {
        "exists": true,
        "line_count": 1,
        "mode": "664",
        "path": "/home/ubuntu/.tunnel_to_philip",
        "sha256": "e179abd206de589bd220f3b05184b6ff5c9c764daa4624eeb409487498361f46"
      }
    ]
  },
  "processes": {
    "absent_control": {
      "count": 0,
      "items": []
    },
    "keeper": {
      "count": 1,
      "items": [
        {
          "cmdline": [
            "/bin/bash",
            "/home/ubuntu/bin/keeper.sh"
          ],
          "fd255": {
            "exists": true,
            "inode": 36197337,
            "sha256": "603a6cc89cd98ed6e2def545c7b0bee362de7eb6a05ac2d6b97759a4bb93e503",
            "target": "/home/ubuntu/bin/keeper.sh"
          },
          "fd9": {
            "exists": true,
            "inode": 35033503,
            "lock_probe_available": false,
            "open_fds_for_lock": [
              {
                "fd": 9,
                "pid": 1071
              }
            ],
            "target": "/home/ubuntu/.keeper.lock",
            "write_flock_held": true
          },
          "pid": 1071,
          "ppid": 1,
          "start_tick": 7893775
        }
      ]
    },
    "m2_sync": {
      "count": 0,
      "items": []
    },
    "ssh_local_forward": {
      "count": 0,
      "items": []
    },
    "syncthing": {
      "count": 2,
      "items": [
        {
          "cmdline": [
            "/home/ubuntu/bin/syncthing",
            "serve",
            "--no-browser"
          ],
          "pid": 1079,
          "ppid": 1071,
          "start_tick": 7893778
        },
        {
          "cmdline": [
            "/home/ubuntu/bin/syncthing",
            "serve",
            "--no-browser"
          ],
          "pid": 1395414,
          "ppid": 1079,
          "start_tick": 164743067
        }
      ]
    }
  }
}
603a6cc89cd98ed6e2def545c7b0bee362de7eb6a05ac2d6b97759a4bb93e503  /home/ubuntu/bin/keeper.sh
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  scripts/sync/keeper.sh
bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  /home/ubuntu/bin/m2-sync.sh
bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  scripts/sync/m2-sync.sh
?? tasks/T-2026-08-13-hub-deploy-lecun-marker-cutover/
sync_alerts_before size=62065 mtime=1786615769
gate_a_probe_rc=0
keeper_expected_mismatch_rc=1
m2_sync_match_rc=0
marker_count=1
marker_path_rc=0
backup_absent_rc=0
603a6cc89cd98ed6e2def545c7b0bee362de7eb6a05ac2d6b97759a4bb93e503  /home/ubuntu/bin/keeper.sh
603a6cc89cd98ed6e2def545c7b0bee362de7eb6a05ac2d6b97759a4bb93e503  /home/ubuntu/bin/keeper.sh.before.T-2026-08-13-hub-deploy-lecun-marker-cutover
e179abd206de589bd220f3b05184b6ff5c9c764daa4624eeb409487498361f46  /home/ubuntu/.tunnel_to_philip
e179abd206de589bd220f3b05184b6ff5c9c764daa4624eeb409487498361f46  /home/ubuntu/.hub-migration-backup.T-2026-08-13-hub-deploy-lecun-marker-cutover/marker.copy
775 /home/ubuntu/bin/keeper.sh
775 /home/ubuntu/bin/keeper.sh.before.T-2026-08-13-hub-deploy-lecun-marker-cutover
664 /home/ubuntu/.tunnel_to_philip
664 /home/ubuntu/.hub-migration-backup.T-2026-08-13-hub-deploy-lecun-marker-cutover/marker.copy
keeper_copy_cmp_rc=0
marker_copy_cmp_rc=0
keeper_canonical_mismatch_rc=1
keeper_modes=775,775
marker_modes=664,664
backup_file_count=1
backup_mode=700
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  /tmp/keeper.T-2026-08-13-hub-deploy-lecun-marker-cutover
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  scripts/sync/keeper.sh
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  /tmp/keeper.T-2026-08-13-hub-deploy-lecun-marker-cutover
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  scripts/sync/keeper.sh
staging mode=755 size=2709 path=/tmp/keeper.T-2026-08-13-hub-deploy-lecun-marker-cutover
deployed_cmp_rc=0
deployed_sha=9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90
canonical_sha=9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90
old_fd255_sha=603a6cc89cd98ed6e2def545c7b0bee362de7eb6a05ac2d6b97759a4bb93e503
e179abd206de589bd220f3b05184b6ff5c9c764daa4624eeb409487498361f46  /home/ubuntu/.hub-migration-backup.T-2026-08-13-hub-deploy-lecun-marker-cutover/marker.copy
e179abd206de589bd220f3b05184b6ff5c9c764daa4624eeb409487498361f46  /home/ubuntu/.hub-migration-backup.T-2026-08-13-hub-deploy-lecun-marker-cutover/.tunnel_to_philip.active
664 /home/ubuntu/.hub-migration-backup.T-2026-08-13-hub-deploy-lecun-marker-cutover/marker.copy
664 /home/ubuntu/.hub-migration-backup.T-2026-08-13-hub-deploy-lecun-marker-cutover/.tunnel_to_philip.active
gate_g3_home_marker_count=0
gate_g3_backup_file_count=2
gate_g3_marker_cmp_rc=0
gate_g3_deployed_cmp_rc=0
gate_g3_staging_cmp_rc=0
{
  "files": {
    "authorized_keys": {
      "exists": true,
      "line_count": 6,
      "mode": "600",
      "path": "/home/ubuntu/.ssh/authorized_keys",
      "sha256": "4e861bdd5c7376d2613300517f2ba7c1412bb2db7abee190c69e05310be1d9db"
    },
    "known_hosts": {
      "exists": true,
      "line_count": 16,
      "mode": "600",
      "path": "/home/ubuntu/.ssh/known_hosts",
      "sha256": "735eccd5c2c8eae141d52252f3aa0c7b45e8b6039715d1fea41e87e7c9a737b2"
    },
    "stignore": {
      "exists": true,
      "line_count": 68,
      "mode": "664",
      "path": "/home/ubuntu/slocal2/m2/.stignore",
      "sha256": "61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a"
    }
  },
  "keeper_lock_available": false,
  "label": "before_term",
  "listeners": {
    "22000": {
      "count": 1,
      "items": [
        {
          "address": "::",
          "family": "tcp6",
          "inode": 27311444,
          "port": 22000
        }
      ]
    },
    "22001": {
      "count": 0,
      "items": []
    },
    "50072": {
      "count": 0,
      "items": []
    },
    "8384": {
      "count": 1,
      "items": [
        {
          "address": "127.0.0.1",
          "family": "tcp",
          "inode": 27303292,
          "port": 8384
        }
      ]
    }
  },
  "markers": {
    "count": 0,
    "items": []
  },
  "processes": {
    "absent_control": {
      "count": 0,
      "items": []
    },
    "keeper": {
      "count": 1,
      "items": [
        {
          "cmdline": [
            "/bin/bash",
            "/home/ubuntu/bin/keeper.sh"
          ],
          "fd255": {
            "exists": true,
            "inode": 36197337,
            "sha256": "603a6cc89cd98ed6e2def545c7b0bee362de7eb6a05ac2d6b97759a4bb93e503",
            "target": "/home/ubuntu/bin/keeper.sh (deleted)"
          },
          "fd9": {
            "exists": true,
            "inode": 35033503,
            "lock_probe_available": false,
            "open_fds_for_lock": [
              {
                "fd": 9,
                "pid": 1071
              }
            ],
            "target": "/home/ubuntu/.keeper.lock",
            "write_flock_held": true
          },
          "pid": 1071,
          "ppid": 1,
          "start_tick": 7893775
        }
      ]
    },
    "m2_sync": {
      "count": 0,
      "items": []
    },
    "ssh_local_forward": {
      "count": 0,
      "items": []
    },
    "syncthing": {
      "count": 2,
      "items": [
        {
          "cmdline": [
            "/home/ubuntu/bin/syncthing",
            "serve",
            "--no-browser"
          ],
          "pid": 1079,
          "ppid": 1071,
          "start_tick": 7893778
        },
        {
          "cmdline": [
            "/home/ubuntu/bin/syncthing",
            "serve",
            "--no-browser"
          ],
          "pid": 1395414,
          "ppid": 1079,
          "start_tick": 164743067
        }
      ]
    }
  }
}
old_keeper_identity_check_rc=0 old_pid=1071
old_pid=1071 elapsed_seconds=0 pid_gone_rc=0 lock_available_rc=0
{
  "files": {
    "authorized_keys": {
      "exists": true,
      "line_count": 6,
      "mode": "600",
      "path": "/home/ubuntu/.ssh/authorized_keys",
      "sha256": "4e861bdd5c7376d2613300517f2ba7c1412bb2db7abee190c69e05310be1d9db"
    },
    "known_hosts": {
      "exists": true,
      "line_count": 16,
      "mode": "600",
      "path": "/home/ubuntu/.ssh/known_hosts",
      "sha256": "735eccd5c2c8eae141d52252f3aa0c7b45e8b6039715d1fea41e87e7c9a737b2"
    },
    "stignore": {
      "exists": true,
      "line_count": 68,
      "mode": "664",
      "path": "/home/ubuntu/slocal2/m2/.stignore",
      "sha256": "61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a"
    }
  },
  "keeper_lock_available": true,
  "label": "before_start",
  "listeners": {
    "22000": {
      "count": 1,
      "items": [
        {
          "address": "::",
          "family": "tcp6",
          "inode": 27311444,
          "port": 22000
        }
      ]
    },
    "22001": {
      "count": 0,
      "items": []
    },
    "50072": {
      "count": 0,
      "items": []
    },
    "8384": {
      "count": 1,
      "items": [
        {
          "address": "127.0.0.1",
          "family": "tcp",
          "inode": 27303292,
          "port": 8384
        }
      ]
    }
  },
  "markers": {
    "count": 0,
    "items": []
  },
  "processes": {
    "absent_control": {
      "count": 0,
      "items": []
    },
    "keeper": {
      "count": 0,
      "items": []
    },
    "m2_sync": {
      "count": 0,
      "items": []
    },
    "ssh_local_forward": {
      "count": 0,
      "items": []
    },
    "syncthing": {
      "count": 2,
      "items": [
        {
          "cmdline": [
            "/home/ubuntu/bin/syncthing",
            "serve",
            "--no-browser"
          ],
          "pid": 1079,
          "ppid": 1,
          "start_tick": 7893778
        },
        {
          "cmdline": [
            "/home/ubuntu/bin/syncthing",
            "serve",
            "--no-browser"
          ],
          "pid": 1395414,
          "ppid": 1079,
          "start_tick": 164743067
        }
      ]
    }
  }
}
{"keeper_pid": 3967705}
{
  "files": {
    "authorized_keys": {
      "exists": true,
      "line_count": 6,
      "mode": "600",
      "path": "/home/ubuntu/.ssh/authorized_keys",
      "sha256": "4e861bdd5c7376d2613300517f2ba7c1412bb2db7abee190c69e05310be1d9db"
    },
    "known_hosts": {
      "exists": true,
      "line_count": 16,
      "mode": "600",
      "path": "/home/ubuntu/.ssh/known_hosts",
      "sha256": "735eccd5c2c8eae141d52252f3aa0c7b45e8b6039715d1fea41e87e7c9a737b2"
    },
    "stignore": {
      "exists": true,
      "line_count": 68,
      "mode": "664",
      "path": "/home/ubuntu/slocal2/m2/.stignore",
      "sha256": "61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a"
    }
  },
  "keeper_lock_available": false,
  "label": "after_start",
  "listeners": {
    "22000": {
      "count": 1,
      "items": [
        {
          "address": "::",
          "family": "tcp6",
          "inode": 27311444,
          "port": 22000
        }
      ]
    },
    "22001": {
      "count": 0,
      "items": []
    },
    "50072": {
      "count": 0,
      "items": []
    },
    "8384": {
      "count": 1,
      "items": [
        {
          "address": "127.0.0.1",
          "family": "tcp",
          "inode": 27303292,
          "port": 8384
        }
      ]
    }
  },
  "markers": {
    "count": 0,
    "items": []
  },
  "processes": {
    "absent_control": {
      "count": 0,
      "items": []
    },
    "keeper": {
      "count": 1,
      "items": [
        {
          "cmdline": [
            "/bin/bash",
            "/home/ubuntu/bin/keeper.sh"
          ],
          "fd255": {
            "exists": true,
            "inode": 36215005,
            "sha256": "9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90",
            "target": "/home/ubuntu/bin/keeper.sh"
          },
          "fd9": {
            "exists": true,
            "inode": 35033503,
            "lock_probe_available": false,
            "open_fds_for_lock": [
              {
                "fd": 9,
                "pid": 3967705
              }
            ],
            "target": "/home/ubuntu/.keeper.lock",
            "write_flock_held": true
          },
          "pid": 3967705,
          "ppid": 1,
          "start_tick": 232784150
        }
      ]
    },
    "m2_sync": {
      "count": 0,
      "items": []
    },
    "ssh_local_forward": {
      "count": 0,
      "items": []
    },
    "syncthing": {
      "count": 2,
      "items": [
        {
          "cmdline": [
            "/home/ubuntu/bin/syncthing",
            "serve",
            "--no-browser"
          ],
          "pid": 1079,
          "ppid": 1,
          "start_tick": 7893778
        },
        {
          "cmdline": [
            "/home/ubuntu/bin/syncthing",
            "serve",
            "--no-browser"
          ],
          "pid": 1395414,
          "ppid": 1079,
          "start_tick": 164743067
        }
      ]
    }
  }
}
{
  "files": {
    "authorized_keys": {
      "exists": true,
      "line_count": 6,
      "mode": "600",
      "path": "/home/ubuntu/.ssh/authorized_keys",
      "sha256": "4e861bdd5c7376d2613300517f2ba7c1412bb2db7abee190c69e05310be1d9db"
    },
    "known_hosts": {
      "exists": true,
      "line_count": 16,
      "mode": "600",
      "path": "/home/ubuntu/.ssh/known_hosts",
      "sha256": "735eccd5c2c8eae141d52252f3aa0c7b45e8b6039715d1fea41e87e7c9a737b2"
    },
    "stignore": {
      "exists": true,
      "line_count": 68,
      "mode": "664",
      "path": "/home/ubuntu/slocal2/m2/.stignore",
      "sha256": "61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a"
    }
  },
  "keeper_lock_available": false,
  "label": "stable",
  "listeners": {
    "22000": {
      "count": 1,
      "items": [
        {
          "address": "::",
          "family": "tcp6",
          "inode": 27311444,
          "port": 22000
        }
      ]
    },
    "22001": {
      "count": 0,
      "items": []
    },
    "50072": {
      "count": 0,
      "items": []
    },
    "8384": {
      "count": 1,
      "items": [
        {
          "address": "127.0.0.1",
          "family": "tcp",
          "inode": 27303292,
          "port": 8384
        }
      ]
    }
  },
  "markers": {
    "count": 0,
    "items": []
  },
  "processes": {
    "absent_control": {
      "count": 0,
      "items": []
    },
    "keeper": {
      "count": 1,
      "items": [
        {
          "cmdline": [
            "/bin/bash",
            "/home/ubuntu/bin/keeper.sh"
          ],
          "fd255": {
            "exists": true,
            "inode": 36215005,
            "sha256": "9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90",
            "target": "/home/ubuntu/bin/keeper.sh"
          },
          "fd9": {
            "exists": true,
            "inode": 35033503,
            "lock_probe_available": false,
            "open_fds_for_lock": [
              {
                "fd": 9,
                "pid": 3967705
              }
            ],
            "target": "/home/ubuntu/.keeper.lock",
            "write_flock_held": true
          },
          "pid": 3967705,
          "ppid": 1,
          "start_tick": 232784150
        }
      ]
    },
    "m2_sync": {
      "count": 0,
      "items": []
    },
    "ssh_local_forward": {
      "count": 0,
      "items": []
    },
    "syncthing": {
      "count": 2,
      "items": [
        {
          "cmdline": [
            "/home/ubuntu/bin/syncthing",
            "serve",
            "--no-browser"
          ],
          "pid": 1079,
          "ppid": 1,
          "start_tick": 7893778
        },
        {
          "cmdline": [
            "/home/ubuntu/bin/syncthing",
            "serve",
            "--no-browser"
          ],
          "pid": 1395414,
          "ppid": 1079,
          "start_tick": 164743067
        }
      ]
    }
  }
}
sync_alerts_after size=62210 mtime=1786616795
2026-08-13 10:26:35 [lecun] 一時停止中: /home/ubuntu/slocal2/m2/.sync-pause があるため分岐へ書き込まない（消せば再開）
gate_g5_stable_state_rc=0
gate_g5_find_marker_count=0
gate_g5_marker_rollback_cmp_rc=0
gate_g5_old_pid_absent_control_rc=2
gate_g5_keeper_backup_rc=0
gate_g5_sync_log_size_before=62065
gate_g5_sync_log_size_after=62210
gate_g5_pause_log_rc=0
rollback=not_run
launcher_argument_control_output=launch_keeper.py does not accept arguments
launcher_argument_control_rc=2
launcher_control_keeper_count=1
