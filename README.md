# ll · 技能库

按独立目录管理AI技能和配套插件。

| 组件 | 用途 |
| --- | --- |
| [吴院公众号排版skill](skills/wjx-wechat-layout/SKILL.md) | AI读取Word和可选配图，完成吴院风格排版，输出含图片的秀米导入包 |
| [吴院推送导入助手](plugins/wjx-xiumi-importer/README.md) | 独立Chrome／Edge插件，把数据包的图片与正文导入秀米 |

## 只需skill＋插件

1. 给AI提供Word和可选图片包，要求使用吴院排版skill。
2. AI交付预览与`article.xiumi.json`。所有配图已装入数据包。
3. 在秀米新建空白图文，插件选择数据包，点击“导入正文与图片”。
4. 在秀米核对标题摘要并保存，重新打开后用插件核验。

不需要工作台、本地HTTP服务或额外AI API Key。排版修改直接在AI对话中提出。

## 安装

技能：将`skills/wjx-wechat-layout`安装到助手技能目录。依赖为Python、python-docx、beautifulsoup4、Pillow。图片打包会校验实际格式，避免文件后缀与数据类型不一致。

插件：下载本仓库，在浏览器扩展管理页开启开发者模式，加载`plugins/wjx-xiumi-importer`文件夹。只需安装一次。

## AI侧命令

```sh
python -m pip install -r skills/wjx-wechat-layout/requirements.txt
python skills/wjx-wechat-layout/scripts/wechat_layout.py extract input.docx --out work/article.json
# AI复核栏目、图文对应关系和结构稿后再运行
python skills/wjx-wechat-layout/scripts/wechat_layout.py render work/article.json --out output
```

render同时生成预览、HTML与`article.xiumi.json`。现有正文HTML可用`scripts/export_xiumi.py`单独打包，不得只更改文件后缀。

10个栏目、19项素材组件；Word内容保留、图片打包、独立导出和模拟秀米导入/重开核验已测试。真实秀米账号权限、图片上传及服务端保存尚待实测。插件不会自动发布。

导入核心复用[OpsLion](https://github.com/Infunus/OpsLion)，源码许可与出处见插件目录。用户稿件、完整公众号样本和本机登录数据不包含在仓库中。
