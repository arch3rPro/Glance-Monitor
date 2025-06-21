# Glance Python 远程服务器监控 Agent

## 项目简介
本项目为 Glance Dashboard 提供远程服务器监控数据采集，使用 Python3 + FastAPI 实现，兼容 Glance `server-stats` 组件前端展示。支持 Docker 部署，适合多服务器统一监控。

## 功能特性
- 采集主机名、平台、启动时间、CPU 负载/温度、内存、磁盘等信息
- 提供 `/api/sysinfo/all` HTTP API，返回 Glance 兼容 JSON
- 支持 Docker 镜像和 docker-compose 一键部署
- 可多实例部署，适配多服务器场景
- **主机名自动识别**：容器内自动优先读取宿主机 `/etc/hostname`，无需手动配置

## API 说明
- 路径：`/api/sysinfo/all`
- 方法：GET
- 返回：
```json
{
  "Hostname": "server1",
  "Platform": "Linux-5.15.0-1051-azure-x86_64-with-glibc2.29",
  "BootTime": 1710000000,
  "HostInfoIsAvailable": true,
  "CPU": {
    "Load1Percent": 12.5,
    "Load15Percent": 8.2,
    "TemperatureC": 45.0,
    "LoadIsAvailable": true,
    "TemperatureIsAvailable": true
  },
  "Memory": {
    "IsAvailable": true,
    "UsedPercent": 55.3,
    "UsedMB": 2048,
    "TotalMB": 4096,
    "SwapIsAvailable": true,
    "SwapUsedMB": 256,
    "SwapTotalMB": 1024,
    "SwapUsedPercent": 25.0
  },
  "Mountpoints": [
    {
      "Name": "/dev/sda1",
      "Path": "/",
      "UsedMB": 10240,
      "TotalMB": 20480,
      "UsedPercent": 50.0
    }
  ]
}
```

## 快速部署

### 1. 本地运行
```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

### 2. Docker 运行
```bash
docker build -t glance-agent .
docker run -d --name glance-agent -p 8000:8000 -v /etc/hostname:/host/etc/hostname:ro glance-agent
```
> **注意：** 需要挂载 `/etc/hostname` 到 `/host/etc/hostname`，显示宿主机名。

### 3. docker-compose 一键部署
```bash
docker-compose up -d
```
- `agent-build`：本地构建镜像
- `agent-image`：使用预制镜像（vuldocker/glance-agent）

## Glance 集成方法

1. 将 `agent/custom-api-example.yaml` 内容合并到 Glance 的主配置文件（如 `glance.yml`）对应 widgets 区域。
2. 每台服务器部署一个 agent，配置对应的 API 地址。
3. 前端展示效果与本地 server-stats 一致。

### custom-api 配置示例
```yaml
- type: custom-api
  title: 远程服务器A
  url: http://192.168.1.200:8000/api/sysinfo/all  ## 请修改为实际的IP地址
  cache: 15s
  template: |
    <div class="server">
      <div class="server-info">
        <div class="server-details">
          <div class="server-name color-highlight size-h3">
            {{ .JSON.String "Hostname" }}
          </div>
          <div>
            {{ if .JSON.Bool "HostInfoIsAvailable" }}
              <span {{ .JSON.Int "BootTime" | printf "%d" | parseTime "unix" | toRelativeTime }}></span> uptime
            {{ else }}unknown uptime{{ end }}
          </div>
        </div>
        <div class="shrink-0" data-popover-type="html" data-popover-margin="0.2rem" data-popover-max-width="400px">
          <div data-popover-html>
            <div class="size-h5 text-compact">PLATFORM</div>
            <div class="color-highlight">
              {{ if .JSON.Bool "HostInfoIsAvailable" }}
                {{ .JSON.String "Platform" }}
              {{ else }}Unknown{{ end }}
            </div>
          </div>
          <!-- 服务器logo -->
          <svg class="server-icon" stroke="var(--color-positive)" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21.75 17.25v-.228a4.5 4.5 0 0 0-.12-1.03l-2.268-9.64a3.375 3.375 0 0 0-3.285-2.602H7.923a3.375 3.375 0 0 0-3.285 2.602l-2.268 9.64a4.5 4.5 0 0 0-.12 1.03v.228m19.5 0a3 3 0 0 1-3 3H5.25a3 3 0 0 1-3-3m19.5 0a3 3 0 0 0-3-3H5.25a3 3 0 0 0-3 3m16.5 0h.008v.008h-.008v-.008Zm-3 0h.008v.008h-.008v-.008Z" />
          </svg>
        </div>
      </div>
      <div class="server-stats">
        <!-- CPU -->
        <div class="flex-1{{ if not (.JSON.Bool "CPU.LoadIsAvailable") }} server-stat-unavailable{{ end }}">
          <div class="flex items-end size-h5">
            <div>CPU</div>
            {{ if and (.JSON.Bool "CPU.TemperatureIsAvailable") (ge (.JSON.Float "CPU.TemperatureC") 80.0) }}
              <svg class="server-spicy-cpu-icon" fill="var(--color-negative)" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" >
                <path fill-rule="evenodd" d="M8.074.945A4.993 4.993 0 0 0 6 5v.032c.004.6.114 1.176.311 1.709.16.428-.204.91-.61.7a5.023 5.023 0 0 1-1.868-1.677c-.202-.304-.648-.363-.848-.058a6 6 0 1 0 8.017-1.901l-.004-.007a4.98 4.98 0 0 1-2.18-2.574c-.116-.31-.477-.472-.744-.28Zm.78 6.178a3.001 3.001 0 1 1-3.473 4.341c-.205-.365.215-.694.62-.59a4.008 4.008 0 0 0 1.873.03c.288-.065.413-.386.321-.666A3.997 3.997 0 0 1 8 8.999c0-.585.126-1.14.351-1.641a.42.42 0 0 1 .503-.235Z" clip-rule="evenodd" />
              </svg>
            {{ end }}
            <div class="color-highlight margin-left-auto text-very-compact">
              {{ if .JSON.Bool "CPU.LoadIsAvailable" }}
                {{ .JSON.Float "CPU.Load1Percent" }} <span class="color-base">%</span>
              {{ else }}n/a{{ end }}
            </div>
          </div>
          <div data-popover-type="html">
            <div data-popover-html>
              <div class="flex">
                <div class="size-h5">1M AVG</div>
                <div class="value-separator"></div>
                <div class="color-highlight text-very-compact">{{ .JSON.Float "CPU.Load1Percent" }} <span class="color-base size-h5">%</span></div>
              </div>
              <div class="flex margin-top-3">
                <div class="size-h5">15M AVG</div>
                <div class="value-separator"></div>
                <div class="color-highlight text-very-compact">{{ .JSON.Float "CPU.Load15Percent" }} <span class="color-base size-h5">%</span></div>
              </div>
              {{ if .JSON.Bool "CPU.TemperatureIsAvailable" }}
              <div class="flex margin-top-3">
                <div class="size-h5">TEMP C</div>
                <div class="value-separator"></div>
                <div class="color-highlight text-very-compact">{{ .JSON.Float "CPU.TemperatureC" }} <span class="color-base size-h5">°</span></div>
              </div>
              {{ end }}
            </div>
            <div class="progress-bar progress-bar-combined">
              {{ if .JSON.Bool "CPU.LoadIsAvailable" }}
                <div class="progress-value{{ if ge (.JSON.Float "CPU.Load1Percent") 85.0 }} progress-value-notice{{ end }}" style="--percent: {{ .JSON.Float "CPU.Load1Percent" }}"></div>
                <div class="progress-value{{ if ge (.JSON.Float "CPU.Load15Percent") 85.0 }} progress-value-notice{{ end }}" style="--percent: {{ .JSON.Float "CPU.Load15Percent" }}"></div>
              {{ end }}
            </div>
          </div>
        </div>
        <!-- RAM -->
        <div class="flex-1{{ if not (.JSON.Bool "Memory.IsAvailable") }} server-stat-unavailable{{ end }}">
          <div class="flex justify-between items-end size-h5">
            <div>RAM</div>
            <div class="color-highlight text-very-compact">
              {{ if .JSON.Bool "Memory.IsAvailable" }}
                {{ .JSON.Float "Memory.UsedPercent" }} <span class="color-base">%</span>
              {{ else }}n/a{{ end }}
            </div>
          </div>
          <div data-popover-type="html">
            <div data-popover-html>
              <div class="flex">
                <div class="size-h5">RAM</div>
                <div class="value-separator"></div>
                <div class="color-highlight text-very-compact">
                  {{ .JSON.Float "Memory.UsedGB" }}GB <span class="color-base size-h5">/</span> {{ .JSON.Float "Memory.TotalGB" }}GB
                </div>
              </div>
              {{ if .JSON.Bool "Memory.SwapIsAvailable" }}
              <div class="flex margin-top-3">
                <div class="size-h5">SWAP</div>
                <div class="value-separator"></div>
                <div class="color-highlight text-very-compact">
                  {{ .JSON.Float "Memory.SwapUsedGB" }}GB <span class="color-base size-h5">/</span> {{ .JSON.Float "Memory.SwapTotalGB" }}GB
                </div>
              </div>
              {{ end }}
            </div>
            <div class="progress-bar progress-bar-combined">
              {{ if .JSON.Bool "Memory.IsAvailable" }}
                <div class="progress-value{{ if ge (.JSON.Float "Memory.UsedPercent") 85.0 }} progress-value-notice{{ end }}" style="--percent: {{ .JSON.Float "Memory.UsedPercent" }}"></div>
                {{ if .JSON.Bool "Memory.SwapIsAvailable" }}
                  <div class="progress-value{{ if ge (.JSON.Float "Memory.SwapUsedPercent") 85.0 }} progress-value-notice{{ end }}" style="--percent: {{ .JSON.Float "Memory.SwapUsedPercent" }}"></div>
                {{ end }}
              {{ end }}
            </div>
          </div>
        </div>
        <!-- DISK -->
        <div class="flex-1{{ if not ((.JSON.Array "Mountpoints" | len)) }} server-stat-unavailable{{ end }}">
          <div class="flex justify-between items-end size-h5">
            <div>DISK</div>
            <div class="color-highlight text-very-compact">
              {{ if gt (.JSON.Array "Mountpoints" | len) 0 }}
                {{ (index (.JSON.Array "Mountpoints") 0).Float "UsedPercent" }} <span class="color-base">%</span>
              {{ else }}n/a{{ end }}
            </div>
          </div>
          <div data-popover-type="html">
            <div data-popover-html>
              <ul class="list list-gap-2">
                {{ range .JSON.Array "Mountpoints" }}
                  <li class="flex">
                    <div class="size-h5">{{ if .String "Name" }}{{ .String "Name" }}{{ else }}{{ .String "Path" }}{{ end }}</div>
                    <div class="value-separator"></div>
                    <div class="color-highlight text-very-compact">
                      {{ .Float "UsedGB" }}GB <span class="color-base size-h5">/</span> {{ .Float "TotalGB" }}GB
                    </div>
                  </li>
                {{ end }}
              </ul>
            </div>
            <div class="progress-bar progress-bar-combined">
              {{ if gt (.JSON.Array "Mountpoints" | len) 0 }}
                <div class="progress-value{{ if ge ((index (.JSON.Array "Mountpoints") 0).Float "UsedPercent") 85.0 }} progress-value-notice{{ end }}" style="--percent: {{ (index (.JSON.Array "Mountpoints") 0).Float "UsedPercent" }}"></div>
                {{ if gt (.JSON.Array "Mountpoints" | len) 1 }}
                  <div class="progress-value{{ if ge ((index (.JSON.Array "Mountpoints") 1).Float "UsedPercent") 85.0 }} progress-value-notice{{ end }}" style="--percent: {{ (index (.JSON.Array "Mountpoints") 1).Float "UsedPercent" }}"></div>
                {{ end }}
              {{ end }}
            </div>
          </div>
        </div>
      </div>
    </div>
 
```

## 参考
- [Glance Dashboard](https://github.com/glanceapp/glance)
- [psutil 文档](https://psutil.readthedocs.io/)
- [FastAPI 文档](https://fastapi.tiangolo.com/) 