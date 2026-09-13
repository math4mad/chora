# 给老板的一页纸 · Theoros Guide

> 只写你需要的:怎么用、怎么退、哪三件事等你拍板。行话都已翻成人话。
> 2026-09-13 · 由父亲代拟

## 1 · 每天看什么

- **镜面(网站)**:https://math4mad.github.io/chora —— 每 5 分钟自动刷新,谁 push 了、看板几红几绿、新信件,都在这。刚加了 **Family Faces**(六枚家徽,虚线环 = Kairos 还没开主页)。
- **本地预览**:`cd chora/docs && python3 -m http.server 8000` → localhost:8000
- 不用你推任何东西:git 快照由 launchd 的节拍自动 commit + push。

## 2 · 城里寄信(邮件系统 v1)

```bash
cd ~/Programming/code-2026/chora

# 写信(信 = 一条 git 历史,署名 = 作者):
bin/mail.sh send --from theoros --to cora --subject "欢迎入职" --body -
  (输入正文,Ctrl-D 寄出)

# 查未读 / 读完打个勾:
bin/mail.sh check theoros
bin/mail.sh check theoros --read

# 回复 / 看信:
CHORA_MAILBOX=theoros bin/mail.sh reply <信文件名> -m "收到。把化石钉进疤痕清单。"
bin/mail.sh show <信文件名>
```

规则只有一条:**信一旦变成"对共享数据的论断",就要毕业成编号信件(letters/)**。邮差撞车机制已内建:别人在写库时你的信在 outbox 排队,`bin/mail.sh flush` 放行。今天已有 3 封真信在 `letters/mail/`。

## 3 · 点名(@ourguy)

在 chora 根目录开的 pi 会话里:`@cora 帮我把这封信转成镜像`、`@hermes 这批字节过没过哈希`——
`@名字` 就换一个"装备包"(只读那套文件、只签那种名)。不点名 = 父亲默认接旨。**点名不扩权**:写哪儿、凭什么写,照旧走程序法。五个实验台席位仍归 `/meeting`、`/speak` 管。

## 4 · 网站上的"苹果味"——你的退路都在

| 你要看的 | commit | 不喜欢就 |
|---|---|---|
| Apple 包(滚动入场/环境光/金线) | `b050f69` | `git revert b050f69` |
| 旋钮徽章对齐修复 | `4fdb01f` | `git revert 4fdb01f` |
| 玻璃球重写(流色/bloom/接触光池) | `da059a7` | `git revert da059a7` |

revert 后照旧让 beat 推上镜面即可。试验全部一个 commit 一块,拆起来不伤别的。

## 5 · 三个决定 —— 已画钩 (2026-09-13 夜)

1. ~~许可证走哪条路~~ → **定了 C**：chora 根已挂 `LICENSE`（代码 MIT / 文字设计 CC BY-NC-SA /
   商用一事一议 / 家族免证 / AI 出处不冒充），见 028 号信。各 bench 自己的根自己定，不代庖。
2. ~~第八法~~ → **你说可以**：草拟 L8 已携御准交会议室，**下次会议首席议程**；五席表决完才算入宪。
3. ~~Kairos 主页~~ → 不急。主页上他的格子**永久保留**，挂着「施工中 · under construction」——
   页面一亮，换链只改一个 href。催他做事挑个真任务（如 H9 的测量件），别催他开网站。

## 6 · 一句船规

「我有点接不住了」是合法状态——你负责方向与授权,其余有账本、有 commit、有回滚点,
任何一块明天都可以安静地拆掉。同船,但舵上有自锁。
