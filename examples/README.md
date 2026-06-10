# 示例合约

`reentrancy/Reentrancy.sol` 包含经典的 reentrancy 漏洞样例，供 Slither 检测与 MVP 验收使用。

## 预置 ZIP（推荐）

仓库已包含可直接上传的示例包：

```
examples/reentrancy-example.zip
```

用于 README 快速开始、Demo 录屏（见 [docs/demo-script.md](../docs/demo-script.md)）及 CI 集成测试。

## 重新打包

如需从源码重新生成 ZIP：

```bash
# Linux / macOS
cd examples/reentrancy && zip -r ../reentrancy-example.zip .

# Windows PowerShell
cd examples/reentrancy
Compress-Archive -Path * -DestinationPath ..\reentrancy-example.zip -Force
```

上传 `reentrancy-example.zip` 到 Web 界面即可完成端到端验收。
