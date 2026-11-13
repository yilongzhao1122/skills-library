# 收录一个技能

先选择一个实际任务，把完成任务所需的调查、操作和验证步骤整理成 skill（供智能助手执行任务的技能）。目录名使用能说明用途的小写英文单词，以连字符连接。

1. 在 `skills/`（技能目录）中建立独立目录，写好 `SKILL.md`（技能执行说明）的名称、选择描述和执行流程。
2. 根据任务加入实际会用到的脚本、模板和参考资料，并在执行说明中链接到它们。
3. 参照[说明模板](../templates/skill-readme.md)，介绍核心功能、工作原理、准备条件、调用方式、交付结果和实际验证记录。
4. 按[写作规范](writing-guide.md)补充术语解释，再使用 Humanizer（文字润色技能）通读润色所有功能描述。
5. 在独立工作目录完成检查，保存适合公开的验证摘要，并核对待提交内容。
6. 在首页索引添加一行，写清用途和能完成的工作，然后提交到 GitHub。

技能目录可以从下面的结构开始，再按任务需要增加文件：

```text
skills/
  <技能名称>/
    README.md
    SKILL.md
    agents/openai.yaml
    scripts/
    assets/
    references/
```

其中 `agents/openai.yaml`（客户端显示配置）保存技能名称、简短介绍和默认调用语句。目录结构与实际交付内容保持一致，配套文件都能从入口找到。

## 运行已有检查

在仓库根目录执行。Linux 侧检查使用临时主目录、回环监听和模拟程序响应，覆盖代理环境恢复、文件权限、安装阶段、凭据传递与终端交互：

```bash
python3 tests/test_autodl.py
```

Windows 侧使用 PowerShell（Windows 命令行工具）和模拟响应，检查本轮执行标记与出口变化识别：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tests\test_windows.ps1
```

实例部署中的网站和模型请求使用技能自己的验收流程，并保存实际结果。
