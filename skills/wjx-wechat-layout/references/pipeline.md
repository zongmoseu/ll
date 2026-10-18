# 结构稿与脚本

依赖Python 3、python-docx、beautifulsoup4；全部本地运行，无API。Playwright/Edge可用于浏览器核验，不是转换脚本的必需依赖。

## JSON示例

```json
{
  "version":1,
  "title":"健雄学子 | 示例标题",
  "column":"人物风采",
  "subtype":"健雄学子",
  "classification_reviewed":true,
  "classification":{"reason":"主体为学生成长经历"},
  "blocks":[
    {"type":"intro","runs":[{"text":"原稿导语。"}]},
    {"type":"heading","level":2,"runs":[{"text":"原稿分节标题"}]},
    {"type":"paragraph","runs":[{"text":"正文"},{"text":"强调部分","bold":true}]},
    {"type":"image","src":"source-images/photo.png","caption":"原稿图注"},
    {"type":"quote","runs":[{"text":"原稿引用。"}]},
    {"type":"credit","runs":[{"text":"文字 | 原稿署名"}]}
  ]
}
```

提取稿还包含source、source_text、warnings；不能改source_text掩盖遗漏。示例文字不能填入用户稿件。直接由对话稿建JSON时也保存原文source_text。

模块：paragraph、heading（level 2/3）、intro、quote、caption、credit、list_item、image、gallery、table。文字runs支持bold/italic/underline/href。http/https/mailto/tel之外的协议会被拒绝；保留链接不代表微信允许点击。

- list_item：marker、level，编号与文本分开。
- image：本地src，可有caption、alt、width、role（例如qr）。已有独立caption段就不重复添图注。
- gallery：images为image字段对象数组，mode默认为stack，可选scroll。
- table：rows为行数组，每行由cell组成；cell包含blocks、colspan、rowspan。
- style_overrides：primary/light/accent/text六位色值，font_size、line_height、letter_spacing。
- theme覆盖栏目默认；CLI的--theme优先。

## Word与文本提取

使用Word Title/标题样式识别主标题；未识别时暂取文件名并提示，绝不猜测删除首段。Heading 1/2转正文二/三级。行内图片按顺序抽取，保留超链接/强调，支持常见列表、普通与合并表格。

浮动图片按锚点顺序，须核对。复杂文本框、脚注尾注、嵌入对象、无法读取图形或编号会报错，避免静默丢失。页眉页脚不当正文；确需其中内容应按原稿用途补入后核对。

Markdown支持常见标题、粗斜体、链接、独占一行的本地图片、引用和简单列表，不承诺完整CommonMark；复杂稿先整理成JSON。原始HTML作为文本，不执行。

## 图片映射

首次article.html使用本地相对路径，仅用于预览或由编辑器接收，不能直接视作可发布图片。将微信上传返回的mmbiz HTTPS地址填入image-map.template.json后重新渲染：

```text
python scripts/wechat_layout.py render 工作目录/article.json --out 交付目录 --image-map 图片映射.json
```

映射键为images/哈希名.png等输出路径；脚本只检查地址形状，不宣称确认账号权限或URL可访问。preview继续用本地图，未填项仍列入checks。脚本不上传图片。

预览复制按钮只负责复制富文本，图片是否被Z0接收须实测。不要把源码直接粘到普通富文本正文。

## 首版验证范围（2026-10-18）

已用DOCX测试稿验证：粗体、行内图片前后文本顺序、超链接、数字/项目符号列表、横纵合并表格、文本框拒绝、正文丢失拦截、文件名占位标题纠正、交付JSON与图片独立迁移重渲染。图片地址映射使用合成地址验证替换行为，不代表真实微信上传。

5种主题以390px宽浏览器离线检查，测试图片均能显示，无页面横向溢出。示例是测试稿，不是正式新闻；真实复杂Word仍需逐稿核对。Z0导入与微信草稿保存尚未验证。

## 内置组件与发布信息

新增component模块，例如`{"type":"component","component":"college-wordmark"}`。组件ID查assets/components.json；可设width、background与原稿已有caption。白字组件默认深红底，普通标识/二维码默认白底；不裁切、不改色、不拉伸。二维码不自动替代报名码，未知归属码不默认加入。导出时组件图片一并复制到images，交付article.json保留相对src便于迁移重渲染。

稿件可提供summary和cover，输出到publication.json；主推封面建议2.35:1、副推1:1，不自动裁人脸或二维码。缺摘要会记入checks，按原稿拟定摘要但不篡改事实。

## 获奖名单表格

实际竞赛稿验证后支持header_rows（表头行数）、column_widths（合计100的百分比数组）和nowrap_name_columns（从0起的姓名列索引）。表格单元格不继承正文两字缩进，压缩段后空隙；指定姓名列中的2–4字中文姓名保持完整。列宽参数适合无横向合并的规整表，复杂合并表优先自动列宽。姓名加粗按原稿保留，不能把非吴院同学也加粗。

## 默认对齐与宽度

image.width_percent省略时为100，以正文内容区为参照，不以屏幕为参照。普通配图不再默认为90%或95%。只有用户明确要求、小图或特殊布局才覆盖。image.width仍可限制头像/二维码等小图的像素上限。正文外层padding为0 10px；普通段落与图片不再叠加横向留白。intro内侧16px、标题底板内侧12px仅为框中文字留白。preview的外层20px留白不属于导入HTML。

## 分区排版与内容守恒

group包含blocks数组，递归组合标题、文字、图片与图注，variant可为section或summary。组不额外增加左右内边距，保证图与段落/区块外沿对齐。speaker用于已有发言人姓名行；end_mark输出装饰END。section_label用于获准补充的分节标题，label须同时写入article.layout_additions，检查记录会列明这些新增文字。新增标题不混入原文校验，原段落、图片顺序和引用仍须保留。

science-sections为可选科创分区主题：淡蓝底、白色内容组、统一蓝色标题标签及短装饰点。不要强制覆盖其他栏目或用户指定主题。图文分组应依据语义，不按固定段落下标套用。

college-account-card是用户提供的宣传部同篇成稿末尾完整名片，组件可设edge_aligned:true使边缘与正文同宽。不复制该稿编辑/审核姓名；名片二维码没有进行实时扫码确认。
