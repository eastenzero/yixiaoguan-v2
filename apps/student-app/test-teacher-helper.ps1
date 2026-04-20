## ============================================================
## 教师端模拟脚本 — 配合 S4 学生端冒烟测试使用
## 用法: 按步骤依次执行下面的命令块
## ============================================================

$BASE = "http://192.168.100.165:8100"

## ── Step 0: 教师登录，获取 Token ──
Write-Host "=== Step 0: 教师登录 ===" -ForegroundColor Cyan
$loginBody = @{ staff_id = "T001"; password = "liangshufeng" } | ConvertTo-Json
$loginRes = Invoke-RestMethod -Uri "$BASE/api/auth/login" -Method POST -Body $loginBody -ContentType "application/json"
$TEACHER_TOKEN = $loginRes.access_token
Write-Host "Teacher Token: $TEACHER_TOKEN"
Write-Host ""

## ── Step 1: 查看所有会话（找到学生 escalate 的那个） ──
Write-Host "=== Step 1: 查看会话列表 ===" -ForegroundColor Cyan
$headers = @{ Authorization = "Bearer $TEACHER_TOKEN" }
$convs = Invoke-RestMethod -Uri "$BASE/api/conversations" -Headers $headers
$convs | ConvertTo-Json -Depth 3 | Write-Host
Write-Host ""

## ── Step 2: 教师接受会话（替换 CONV_ID） ──
## ⚠️ 请把下面的数字替换为实际的 conversation id
$CONV_ID = Read-Host "请输入要接受的会话 ID"
Write-Host "=== Step 2: 接受会话 $CONV_ID ===" -ForegroundColor Cyan
try {
    $acceptRes = Invoke-RestMethod -Uri "$BASE/api/conversations/$CONV_ID/accept" -Method POST -Headers $headers
    Write-Host "Accept 成功:" ($acceptRes | ConvertTo-Json)
} catch {
    Write-Host "Accept 失败: $_" -ForegroundColor Red
}
Write-Host ""

## ── Step 3: 教师发送消息 ──
Write-Host "=== Step 3: 教师发送消息 ===" -ForegroundColor Cyan
$msgBody = @{ content = "同学你好，我是梁老师，关于你的问题我来回答一下。" } | ConvertTo-Json
try {
    $sendRes = Invoke-RestMethod -Uri "$BASE/api/conversations/$CONV_ID/messages" -Method POST -Body $msgBody -ContentType "application/json" -Headers $headers
    Write-Host "发送成功:" ($sendRes | ConvertTo-Json)
} catch {
    Write-Host "发送失败: $_" -ForegroundColor Red
}
Write-Host ""

## ── Step 4: 教师解决会话 ──
$doResolve = Read-Host "是否解决该会话？(y/n)"
if ($doResolve -eq "y") {
    Write-Host "=== Step 4: 解决会话 ===" -ForegroundColor Cyan
    try {
        $resolveRes = Invoke-RestMethod -Uri "$BASE/api/conversations/$CONV_ID/resolve" -Method POST -Headers $headers
        Write-Host "Resolve 成功:" ($resolveRes | ConvertTo-Json)
    } catch {
        Write-Host "Resolve 失败: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== 教师模拟完成 ===" -ForegroundColor Green
Write-Host "请回到浏览器查看学生端是否实时收到了教师消息和状态变更。"
