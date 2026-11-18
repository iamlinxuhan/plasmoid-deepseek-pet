#!/bin/sh
# 采样一次 CPU 占用率与内存占用率，输出 "cpu% mem%"，供 Plasma5Support 的 executable 数据源读取。
# CPU 用 /proc/stat 前后 1 秒的差值；内存用 MemTotal 与 MemAvailable。

read -r _ u1 n1 s1 i1 w1 irq1 sirq1 st1 _ < /proc/stat
t1=$((u1 + n1 + s1 + i1 + w1 + irq1 + sirq1 + st1))
idle1=$((i1 + w1))

sleep 1

read -r _ u2 n2 s2 i2 w2 irq2 sirq2 st2 _ < /proc/stat
t2=$((u2 + n2 + s2 + i2 + w2 + irq2 + sirq2 + st2))
idle2=$((i2 + w2))

dt=$((t2 - t1))
di=$((idle2 - idle1))
cpu=$(awk -v dt="$dt" -v di="$di" 'BEGIN { if (dt <= 0) print 0; else printf "%.0f", 100 * (1 - di / dt) }')
mem=$(awk '/^MemTotal:/ { t = $2 } /^MemAvailable:/ { a = $2 } END { if (t <= 0) print 0; else printf "%.0f", 100 * (t - a) / t }' /proc/meminfo)

echo "$cpu $mem"
