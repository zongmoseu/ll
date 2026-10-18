# 独立插件流程

主流程：用户将Word和可选图片包交给AI → 本skill生成article.xiumi.json → 独立插件导入秀米。排版在AI对话中完成；不要求用户启动本地服务、配置工作台或自己调滑块。

插件仓库：https://github.com/zongmoseu/ll/tree/main/plugins/wjx-xiumi-importer

在Edge/Chrome扩展页开启开发者模式，加载已解压的插件目录。以后在秀米登录并新建空白图文，选择.xiumi.json，点击“导入正文与图片”。完成后由用户在秀米保存，重新打开后点击核验。插件内显示标题与摘要供核对填写。

数据包基于OpsLion的xiumi-bridge/v3结构，但由skill中的纯Python脚本直接生成，不依赖OpsLion工作台。正文模块和图片资源引用使用该兼容协议；所有本地图片以base64嵌入一次，插件上传后替换为秀米地址。不能通过把HTML改后缀来生成此包。

插件仅使用activeTab/scripting/storage/unlimitedStorage及秀米域名权限，无localhost、工作台、采集模板、剪贴板或模型API依赖。不会自动发布。

当前完成：独立导出、真实稿件8项图片打包、模拟编辑器导入与保存重开核验。真实秀米账号权限、上传和服务端保存尚待用户实际验证。不得宣称自动获得会员HTML导入权限。

旧references/wechat-z0.md属于历史兼容参考；与本文件冲突时，以当前“skill＋独立秀米插件”流程为准。
