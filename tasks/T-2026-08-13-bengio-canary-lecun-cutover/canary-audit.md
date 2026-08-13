{
  "files": {
    "authorized_keys": {
      "bytes": 2227,
      "exists": true,
      "line_count": 3,
      "mode": "664",
      "mtime_ns": 1782058984239997340,
      "path": "/home/ubuntu/.ssh/authorized_keys",
      "sha256": "c5e26e9a4d75205951d3899c06c4fbd8ab73879b65263548a0f0eebdcf264aab"
    },
    "keeper": {
      "bytes": 2250,
      "exists": true,
      "line_count": 34,
      "mode": "775",
      "mtime_ns": 1783149429220058754,
      "path": "/home/ubuntu/bin/keeper.sh",
      "sha256": "603a6cc89cd98ed6e2def545c7b0bee362de7eb6a05ac2d6b97759a4bb93e503"
    },
    "known_hosts": {
      "bytes": 4054,
      "exists": true,
      "line_count": 13,
      "mode": "600",
      "mtime_ns": 1782125133578824372,
      "path": "/home/ubuntu/.ssh/known_hosts",
      "sha256": "50a529d298ef93ce0baf60db394da5bb728839f5b89f9ee8c7a38764d0925fe3"
    },
    "m2_sync": {
      "bytes": 7342,
      "exists": true,
      "line_count": 133,
      "mode": "775",
      "mtime_ns": 1786619753369828688,
      "path": "/home/ubuntu/bin/m2-sync.sh",
      "sha256": "bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f"
    },
    "stignore": {
      "bytes": 2223,
      "exists": true,
      "line_count": 68,
      "mode": "664",
      "mtime_ns": 1786619753377828813,
      "path": "/home/ubuntu/slocal2/m2/.stignore",
      "sha256": "61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a"
    },
    "sync_alerts": {
      "bytes": 61056,
      "exists": true,
      "line_count": 886,
      "mode": "664",
      "mtime_ns": 1786619753384828923,
      "path": "/home/ubuntu/claude-sync/sync-alerts.log",
      "sha256": "beebb824435e2a88c0ec4b19c43e2c2577a6d587a99f54330b22e433e1d6a193"
    },
    "sync_pause": {
      "bytes": 0,
      "exists": true,
      "line_count": 0,
      "mode": "664",
      "mtime_ns": 1786619382736136505,
      "path": "/home/ubuntu/slocal2/m2/.sync-pause",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    "syncthing_config": {
      "bytes": 21750,
      "exists": true,
      "line_count": 395,
      "mode": "600",
      "mtime_ns": 1783149574437656247,
      "path": "/home/ubuntu/.local/state/syncthing/config.xml",
      "sha256": "86cf69777696da1394739142d93667f9ec31b9be300159563ea0679d23986cd1"
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
          "inode": 384929,
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
          "inode": 418116,
          "port": 8384
        }
      ]
    }
  },
  "markers": {
    "count": 1,
    "items": [
      {
        "bytes": 44,
        "exists": true,
        "hub_address": "philip",
        "key_path": "/home/ubuntu/.ssh/id_ed25519_bengiotophilip",
        "line_count": 1,
        "mode": "664",
        "mtime_ns": 1783121766855297554,
        "path": "/home/ubuntu/.tunnel_to_philip",
        "sha256": "b2c4cbd3e3d1c821e81fc18c2dae53620be1385b5b31d21e0a110726ee711c13"
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
            "inode": 92947459,
            "sha256": "603a6cc89cd98ed6e2def545c7b0bee362de7eb6a05ac2d6b97759a4bb93e503",
            "target": "/home/ubuntu/bin/keeper.sh"
          },
          "fd9": {
            "exists": true,
            "inode": 92668204,
            "lock_probe_available": false,
            "open_fds_for_lock": [
              {
                "fd": 9,
                "pid": 773
              }
            ],
            "target": "/home/ubuntu/.keeper.lock",
            "write_flock_held": true
          },
          "pid": 773,
          "ppid": 1,
          "start_tick": 955479
        }
      ]
    },
    "m2_sync": {
      "count": 0,
      "items": []
    },
    "ssh_forward_lecun": {
      "count": 0,
      "items": []
    },
    "ssh_forward_philip": {
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
          "pid": 2070,
          "ppid": 789,
          "start_tick": 2539289
        },
        {
          "cmdline": [
            "/home/ubuntu/bin/syncthing",
            "serve",
            "--no-browser"
          ],
          "pid": 789,
          "ppid": 773,
          "start_tick": 955480
        }
      ]
    }
  }
}
{
  "label": "center-before",
  "ssh": {
    "host": "192.168.196.176",
    "port": 50072,
    "returncode": 0
  },
  "state": {
    "files": {
      "authorized_keys": {
        "bytes": 1693,
        "exists": true,
        "line_count": 6,
        "mode": "600",
        "path": "/home/ubuntu/.ssh/authorized_keys",
        "sha256": "4e861bdd5c7376d2613300517f2ba7c1412bb2db7abee190c69e05310be1d9db"
      },
      "keeper": {
        "bytes": 2709,
        "exists": true,
        "line_count": 52,
        "mode": "755",
        "path": "/home/ubuntu/bin/keeper.sh",
        "sha256": "9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90"
      }
    },
    "keeper_lock_available": false,
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
      "keeper": {
        "count": 1,
        "items": [
          {
            "fd255": {
              "exists": true,
              "inode": 36215005,
              "sha256": "9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90",
              "target": "/home/ubuntu/bin/keeper.sh"
            },
            "fd9": {
              "exists": true,
              "inode": 35033503,
              "target": "/home/ubuntu/.keeper.lock"
            },
            "pid": 3967705,
            "ppid": 1,
            "start_tick": 232784150
          }
        ]
      },
      "ssh_local_forward": {
        "count": 0,
        "items": []
      },
      "syncthing": {
        "count": 2,
        "items": [
          {
            "pid": 1079,
            "ppid": 1,
            "start_tick": 7893778
          },
          {
            "pid": 1395414,
            "ppid": 1079,
            "start_tick": 164743067
          }
        ]
      }
    }
  }
}

## G1 ユーザー確認

- 確認: bengioのlocal consoleまたはSSHとは独立した復旧経路を現在保持しているか。
- ユーザー回答（逐語）: 「ssh接続でしか操作できない」
- 判定: G1 stop。keeper、marker、SSH中継、Syncthing device addressは変更しない。
