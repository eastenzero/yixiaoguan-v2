#!/bin/bash
# 导出 yx_postgres / yx_redis 的真实 docker 运行参数,用于写 compose 文件
set +e

for c in yx_postgres yx_redis; do
  echo "=============================="
  echo "== $c =="
  echo "=============================="
  docker inspect "$c" --format '
IMAGE: {{.Config.Image}}
CMD: {{.Config.Cmd}}
ENV:
{{range .Config.Env}}  {{.}}
{{end}}
MOUNTS:
{{range .Mounts}}  [{{.Type}}] {{.Source}} -> {{.Destination}} (rw={{.RW}})
{{end}}
PORTS:
{{range $p, $b := .NetworkSettings.Ports}}  {{$p}} -> {{range $b}}{{.HostIp}}:{{.HostPort}} {{end}}
{{end}}
NETWORKS:
{{range $k, $v := .NetworkSettings.Networks}}  {{$k}} = {{$v.IPAddress}}
{{end}}
RESTART: {{.HostConfig.RestartPolicy.Name}}
'
done
