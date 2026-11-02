# Task F の問い合わせ（読むだけ）。両ホストで同じ命令を回す。装置の設定は変えない。
echo "## date"; date -Is
echo "## gpu"; nvidia-smi --query-gpu=index,name,uuid,vbios_version,driver_version,memory.total,power.limit,power.default_limit,power.max_limit,power.min_limit,enforced.power.limit,clocks.max.sm,clocks.max.memory,clocks.sm,clocks.mem,persistence_mode,ecc.mode.current,ecc.mode.pending,pcie.link.gen.current,pcie.link.gen.max,pcie.link.gen.gpumax,pcie.link.gen.hostmax,pcie.link.width.current,pcie.link.width.max,utilization.gpu,memory.used,pstate,temperature.gpu,power.draw,compute_mode,pci.bus_id --format=csv
echo "## gpu_nonexistent (index 7)"; nvidia-smi -i 7 --query-gpu=index,name --format=csv; echo "rc=$?"
echo "## compute apps"; nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
echo "## topo"; nvidia-smi topo -m
echo "## nvidia-smi version"; nvidia-smi --version 2>/dev/null | head -5
echo "## iommu cmdline"; cat /proc/cmdline
echo "## iommu groups"; ls /sys/kernel/iommu_groups 2>&1 | wc -l; ls /sys/class/iommu 2>&1
for b in $(nvidia-smi --query-gpu=pci.bus_id --format=csv,noheader); do d=$(echo $b | tr 'A-F' 'a-f' | sed 's/^0000\(0000\)\?:/0000:/'); echo "gpu $b -> $(readlink /sys/bus/pci/devices/$d/iommu_group 2>&1)"; done
echo "## dmesg iommu"; (dmesg 2>&1 | grep -i -E "iommu|dmar|amd-vi" | head -5) 2>&1
echo "## cpu"; lscpu | grep -E "^(Model name|CPU\(s\)|Thread|Core|Socket|NUMA node|NUMA node[0-9] CPU|Architecture)"
echo "## numa gpu"; for b in $(nvidia-smi --query-gpu=pci.bus_id --format=csv,noheader); do d=$(echo $b | tr 'A-F' 'a-f' | sed 's/^0000\(0000\)\?:/0000:/'); echo "gpu $b numa_node=$(cat /sys/bus/pci/devices/$d/numa_node 2>&1)"; done
echo "## mem"; grep -E "^(MemTotal|MemAvailable|SwapTotal)" /proc/meminfo
echo "## cgroup"; cat /proc/self/cgroup; for f in memory.max memory.high cpu.max pids.max; do printf "%s=" $f; cat /sys/fs/cgroup/$f 2>&1; done
echo "## container"; ls -la /.dockerenv 2>&1; cat /run/systemd/container 2>&1; (systemd-detect-virt -c 2>&1); grep -c -E "docker|containerd|kubepods|lxc" /proc/1/cgroup
echo "## fs"; df -B1 --output=source,fstype,size,used,avail,target ~/slocal2/m2 ~/slocal2/m2/data ~ /tmp; findmnt -T ~/slocal2/m2 -o SOURCE,FSTYPE,OPTIONS
echo "## kernel"; uname -a; cat /etc/os-release | grep -E "^(PRETTY_NAME|VERSION_ID)"
echo "## nvcc gcc"; /usr/local/cuda/bin/nvcc --version | tail -2; gcc --version | head -1
echo "## libs"; ldconfig -p | grep -E "libcudnn\.so|libnccl\.so|libcudart\.so" | head
