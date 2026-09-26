# AstrBot Plugin: BYR Docs & Guide & Curri. 

## Acknowledgement

A ***lot*** of codes borrowed from Nemoyuzx's [Where-to-study](https://github.com/Nemoyuzx/where_to_study)

Codes mainly written by DeepSeek v4.1f

## Usage

在下载好该插件后，虽然会自动安装依赖，但还不能直接使用，还需进行以下步骤

### Playwright

首先，我们要进入当前Python环境

如 `uv` :

```bash(Linux)
source .venv/bin/activate
```
>[!TIP]
> 如果是Windows的话需要
>```
>.venv\Scripts\activate
>```

然后再安装浏览器（全部）
```
playwright install
```
或者选一个安装
```
playwright install chromium
```

### Configurate the Plugin

按需在插件设置里面写入学号/密码（教务/教学云）

>[!TIP]
>所有数据都会存在本地
>
>对于数据处理及获取部分请参见[wts-py](https://github.com/xiewoc/wts_py)或者[Where-to-study](https://github.com/Nemoyuzx/where_to_study)

### Fin

按理来说，到这一步您已经配置好了该插件，如果过程中遇到了任何问题，欢迎提issue

## 复用

对于python代码的复用，可见于[wts-py](https://github.com/xiewoc/wts_py)，并已经提供[wts_bridge.py](https://github.com/xiewoc/wts_py/blob/main/wts_bridge.py)供简易使用

## License

本插件遵循主仓库的GPL 3.0许可