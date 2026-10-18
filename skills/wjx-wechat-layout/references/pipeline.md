# 结构稿与执行

Python依赖见requirements.txt。主流程：extract → AI复核与分组 → render → 手机预览检查 → article.xiumi.json，由独立秀米插件导入。

```sh
python scripts/wechat_layout.py extract input.docx --out work/article.json
python scripts/wechat_layout.py render work/article.json --out output
```

## 结构稿

顶层包含version、title、column、subtype、classification_reviewed、source_text、blocks；新稿theme默认wjx-sections，所有栏目共用。CLI --theme覆盖稿件显式theme，稿件theme覆盖栏目默认。旧science-sections同样可用。

先读原稿再设置classification_reviewed:true。不要改source_text来掩盖遗漏；确实获准改文才设user_authorized_text_changes。Word标题未识别时，确认首段是真正标题后，将该段移到title并从blocks移除，全文仍须守恒。

## 模块

- paragraph、heading（level 2/3）、intro、quote、caption、credit：runs含text及可选bold/italic/underline/href；paragraph可indent:false。通常用group包裹段落代替再次嵌套intro样式。
- group：blocks递归数组，variant为intro、section、summary。统一主题中使用对应细框与留白。
- section_label：新增导航标题，label必须同时出现在layout_additions；不计为原稿内容。end_mark输出装饰END。
- image：本地src，width_percent默认90，可有width像素上限、alt、caption。独立caption段存在时勿重复加图注。图片不裁切，检查占屏高度。
- gallery：images为各自独立的image对象，mode默认stack；也可直接使用连续image模块。不得用一张合成大图代替多张照片，默认不并排；scroll仅用户要求时启用并在真实秀米保存后验证。Word预拼图须先视觉检查，清晰边界经拆分后生成多个image，记录来源及像素区域；不要误拆海报和名片。
- list_item：marker和level，编号与文本分开。
- table：rows为cell数组，cell包含blocks、colspan、rowspan；header_rows、column_widths（合计100）、nowrap_name_columns用于表头、规整表列宽与姓名不拆行。复杂长表不要缩小到不可读。
- component：component为assets/components.json中的ID；可设置width、background、edge_aligned。college-account-card为完整学院名片，保持原样，不沿用参考稿署名。
- unresolved_media：保留未处理Word图形位置；解决前can_export:false。

## 元数据与主题

summary、cover写入publication.json，供后台单独设置，不混入正文。缺摘要需按稿件拟定；不编造封面。style_overrides可调整主题色和样式：primary/light/accent/text、font_size、line_height、letter_spacing、page_background、group_border、group_padding、summary_padding。用户最新明确要求优先。

## 提取限制

支持.docx、Markdown、文本；旧.doc先真正转换。保留行内图片顺序与文字强调，浮动图按锚点，需人工核对。VML横线转为divider，暂不支持的绘图保留占位。修订、公式、未能读取的文本框、脚注尾注会提示处理，不静默遗漏。

无需列表的合法Word可没有numbering.xml；有编号却缺定义时应报错，不能删除编号继续。

## 导出与核验

render生成article.xiumi.json、preview.html、article.html、images/、可迁移article.json、publication.json、checks.json。最终提供JSON与预览链接，不只贴JSON文本。图片必须内嵌，图片MIME依据真实字节；静态WebP/AVIF转PNG，动态不能静默变静态。

检查can_export、xiumi_package_generated、text_preserved，数据包assetSummary.local为0。以390–430px看开头、正文、表格、照片与结尾，不仅检查溢出。模拟通过不代表真实秀米导入、保存、重开均通过。

备用HTML可用scripts/export_xiumi.py独立打包。image-map仅供备用微信HTML映射，不改变主流程。预览页工具栏的复制功能不是主交付；不要把源码粘到普通编辑区。
