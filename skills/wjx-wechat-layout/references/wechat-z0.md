# 历史兼容参考

用户已改为“AI排版skill＋独立插件导入秀米”，不使用工作台，也不以Z0为主流程。当前说明见xiumi-plugin.md；下文保留为HTML兼容经验。

# 微信与Z0适配

用户已明确目标为：生成HTML，经Z0编辑器导入微信公众号后台。此路径已确定，不再询问是否使用秀米；秀米只出现在培训原文中，其操作流程不参与本技能。

默认交付供Z0导入的article.html、预览、图片和publication.json。具体按钮/API及图片接收行为尚未实测，不编造界面名称，不宣称已完成导入。没有实际导入并保存微信预览前，z0_import_verified保持false。需要自动控制Z0时才查明产品版本和实际接口；不阻塞本地HTML生成。

## 兼容性

- 正文内联样式，不包含预览工具栏、复制脚本、微信导航点赞栏，不依赖JS或外部CSS。
- 本地路径、data URI和浏览器显示的远程图不等于可发布素材；须编辑器接收或转微信地址。
- 图片等比缩放，不裁二维码；GIF保留格式，上传后的播放效果须检查。
- 滑动图集、SVG和特殊排版在导入后保存草稿，再用手机预览。浏览器效果不能证明微信兼容性。
- 生成HTML的授权不包含自动登录、上传、写草稿或发布。

## 用户提供的SVG参考

[IF-Link-Tech-Team / wechat-svg](https://github.com/IF-Link-Tech-Team/awesome-IF.Link/blob/main/公众号/公众号%20SVG%20约束/SKILL.md)提供社区兼容性经验，包括避免defs/marker/url(#id)依赖、内联箭头路径、显式宽高与viewBox、避免foreignObject和动画属性白名单。

这些不是已核实的官方永久规则。需要SVG再参考并实测；普通HTML无需深层g编组或变换抵消链。统一begin=click、fill=freeze、restart=never是特定交互方案约束，不能套到所有动画。SVG的id/class建议也不能套到本地预览复制按钮。

若继续采集原文：本次普通HTTP曾返回验证页，而正常Edge浏览器可读取正文。可先尝试浏览器，确认#js_content后保存并补齐data-src图片。遇到验证不得把验证页当文章，也不承诺绕过验证。
