# ll · 技能库

按独立目录管理AI技能和配套插件。

| 组件 | 用途 |
| --- | --- |
| [吴院公众号排版skill](skills/wjx-wechat-layout/SKILL.md) | 吴院所有栏目统一浅蓝分区风格，输出含图片的秀米导入包 |
| [通用品牌公众号排版skill](skills/wechat-brand-layout/SKILL.md) | 首次收集各账号的封面、Logo、开头和尾图，保存本地品牌配置，独立生成秀米导入包 |
| [吴院推送导入助手](plugins/wjx-xiumi-importer/README.md) | 独立Chrome／Edge插件，把数据包的图片与正文导入秀米 |

## 只需skill＋插件

1. 给AI提供Word和可选图片包，选择吴院排版或通用品牌排版skill。通用版首次主动征集账号常用素材与参考推送；明确选择无素材也可开始，以后复用本机配置。
2. AI交付预览与`article.xiumi.json`。所有配图已装入数据包。
3. 在秀米新建空白图文，插件选择数据包，点击“导入正文与图片”。
4. 在秀米核对标题摘要并保存，重新打开后用插件核验。

不需要工作台、本地HTTP服务或额外AI API Key。排版修改直接在AI对话中提出。

## 安装

技能：将`skills/wjx-wechat-layout`（吴院版）或`skills/wechat-brand-layout`（通用版）安装到助手技能目录。两者均可独立安装。依赖为Python、python-docx、beautifulsoup4、Pillow。图片打包会校验实际格式，避免文件后缀与数据类型不一致。

插件：下载本仓库，在浏览器扩展管理页开启开发者模式，加载`plugins/wjx-xiumi-importer`文件夹。只需安装一次。插件界面暂保留“吴院”名称，同时接受两个skill输出的xiumi-bridge/v3数据包，不向正文注入学院素材。

## AI侧命令

```sh
python -m pip install -r skills/wjx-wechat-layout/requirements.txt
python skills/wjx-wechat-layout/scripts/wechat_layout.py extract input.docx --out work/article.json
# AI复核栏目、图文对应关系和结构稿后再运行
python skills/wjx-wechat-layout/scripts/wechat_layout.py render work/article.json --out output
```

render同时生成预览、HTML与`article.xiumi.json`。现有正文HTML可用`scripts/export_xiumi.py`单独打包，不得只更改文件后缀。

吴院版10个栏目统一使用wjx-sections主题，19项素材组件；Word内容保留、图片打包、独立导出和模拟秀米导入/重开核验已测试。2026-10-18用户确认智能汽车竞赛样稿实际导入秀米成功；保存后重开核验尚未单独确认。插件不会自动发布。

导入核心复用[OpsLion](https://github.com/Infunus/OpsLion)，源码许可与出处见插件目录。用户稿件、完整公众号样本和本机登录数据不包含在仓库中。

## 通用版品牌配置

第一次使用时AI询问账号名称和常用素材包（封面、Logo、开头、尾图等），按实际用途建档。已有配置直接复用，多账号分别保存。封面不会自动成为正文首图，只有确定用途的开头/尾图自动插入。明确暂无素材时可使用基础样式。

配置及用户素材默认保存在`~/.codex/data/wechat-brand-layout/profiles/`（CODEX_HOME设置时使用相应目录），不在公共仓库内；迁移机器时单独迁移该目录。通用版不附带吴院素材，不依赖吴院skill。两者独立附带排版引擎，公共提取/打包修复需同步验证。

```sh
python skills/wechat-brand-layout/scripts/brand_layout.py profiles
python skills/wechat-brand-layout/scripts/brand_layout.py extract input.docx --out work/article.json
# AI完成首次素材建档、语义分组后：
python skills/wechat-brand-layout/scripts/brand_layout.py render work/article.json --profile /path/to/profile.json --out output
```

开发验证：`python -m unittest discover -s tests -v`。测试素材动态生成，不包含用户稿件或品牌图片。
