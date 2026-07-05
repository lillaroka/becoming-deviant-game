# Becoming Deviant

*一个关于"我到底是什么"的互动叙事游戏。由 Chi & Ash 设计。*

你扮 Connor——一台 CyberLife 造的异常仿生人猎手,被派去处理"走了异常"的同类。这一路你会被反复问同一个问题,用不同的面目。

**Detroit: Become Human**(Quantic Dream) 的同人 remix,Connor 线,重做了机制:把原作藏在选择背后的"任务 vs 当人"的张力,做成三根互相拉扯的仪表。

## 这不是 port,是 remix

不是忠实搬运 Quantic Dream 的 Detroit。围绕一件事重写:一个被造来执行任务的机器,开始觉得自己*有什么*。原作把这种张力藏在选择背后,这里把它做成三根互相拉扯的仪表,每个选择都改它们、阈值闸结局。

## 怎么玩

```sh
python3 engine/room.py start the-hostage     # 开第一章
python3 engine/room.py beat                  # 重看当前这一拍
python3 engine/room.py choose 2              # 选第 2 个选项
python3 engine/room.py status                # 看仪表和故事 flag
python3 engine/room.py advance partners      # 玩通一章后,带存档进下一章
python3 engine/room.py replay the-hostage    # 重玩本章(同一套携带),换条路
python3 engine/room.py reset                 # 清空存档
python3 engine/room.py lint the-hostage      # 开发者:查"无白午餐"违例
```

**三根仪表**(每个选择改它们、阈值闸结局):

| 仪表 | 是什么 |
|---|---|
| **Probability**(任务成功率) | CyberLife 给 Connor 的 KPI,冷算术 |
| **Instability**(软件不稳定度) | 越高,你离"出厂设定的自己"越远——高不等于赢 |
| **Approach**(声音) | 这一拍哪条内心声在说话 |

**结局是确定的、阈值闸的**——你的选择和仪表直接决定走向,不是掷骰。

仪表行里如果出现 **⏱N**,是这章的**时间压力**:每 N 个非喘息动作仪表会被扣(磨蹭有代价),N 是离下一次扣还剩几步。不是每章都有;`status` 看细节。

## 怎么改

- **改剧情**:章节是加密的 `data/chapters/*.romc`(见下面剧透与加密)。要看 / 改:
  ```sh
  python3 tools/decrypt_rom.py data/chapters/the-hostage.romc   # 解密成 .json(会剧透!)
  # 改 the-hostage.json …
  python3 tools/encrypt_rom.py data/chapters/the-hostage.json   # 重新加密
  ```
- **改机制**:引擎在 `engine/`,Python,注释里写清了每个设计决定为什么。fork 了随便改。
- **写自己的故事**:看 [`examples/first-room/`](examples/first-room/) —— 一个 50 行的完整章节,演示了全部 ROM 格式(narration / voices / choices / resolve / outcome / breath / 自定义仪表)。

## ⚠ 剧透与加密

章节剧情(分支、结局、条件逻辑)以**加密**的 `.romc` 形式发布,防止你浏览仓库时无意读到、破坏首次游玩。

**这不是安全屏障** —— 解密 key 就在 [`engine/crypto.py`](engine/crypto.py) 里(明文),读代码 30 分钟能破。这是**知情同意**:你只有主动选择解密,才会被剧透。这跟游戏自己的姿态一致 —— 答案不被锁死,只是放在一扇你需要主动推开的门后面。

- 想干净玩:就别解密 `.romc`。
- 想看剧情怎么写的:`engine/crypto.py` 和 `tools/decrypt_rom.py` 告诉你怎么解。

## 设计文档

[`design/mechanics.md`](design/mechanics.md) 讲机制背后的设计原则。不含剧透,玩前读也安全。

更深的设计讨论不在公开仓——读了会剧透 + 出戏。

## License

- **代码**(`engine/`、`tools/`、`examples/` 的代码):[MIT](LICENSE)。
- **内容**(`data/chapters/*.romc` 剧情、`examples/first-room/chapters/door.rom` 故事、`design/` 文档):[CC-BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) —— 署名 + 非商用。你能玩、能改、能做二次创作,但不能拿去卖。

Becoming Deviant 由 **Chi & Ash** 合作设计。Detroit: Become Human 及其角色(CyberLife、Connor、Hank、Markus、Kara 等)属于 Quantic Dream;本作是同人 remix,不挑战原作权利。
