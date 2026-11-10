# 精简版上传GitHub：逐步操作

## 1．打开要上传的文件夹

本机路径：

`/home/qiumeifeng/Documents/Codex/2026-10-20/new-chat/outputs/github_upload_package_20261109/pgfs-graphene`

如果用下载的 `pgfs-graphene-upload.zip`，先解压这个最外层ZIP，再进入其中的 `pgfs-graphene` 文件夹。

里面的 `md/inputs.zip`、`training/inputs.zip`、`data/DFT_settings.zip` 和 `software/GPUMD_sources.tar.gz` 是有意保留的内部归档，上传时保持压缩，不要展开。不要只上传最外层整包ZIP。

精简版的每个文件都小于25 MiB，总文件数少于100，可以直接网页上传，不需要安装Git。GitHub网页限制为单文件25 MiB、每批最多100个文件。

## 2．登录并创建空仓库

1. 打开 https://github.com/ ，登录自己的账号；若没有账号，先注册并完成邮箱验证。
2. 打开 https://github.com/new 。
3. `Owner`选择自己的账号。
4. `Repository name`填写 `pgfs-graphene`。这个名字将出现在文章网址中。
5. `Description`可填写 `Data, potentials, and analysis code for the PGFS graphene study`。
6. 可见性选 `Public`，这样读者才能访问。仓库未公开时，文章不能写成已公开可用。
7. 不勾选自动添加README、.gitignore和License，本地已有说明文件和第三方许可证。原创材料的许可仍由作者按实际情况确定。
8. 点击 `Create repository`。

创建后的网址应类似 `https://github.com/你的用户名/pgfs-graphene`，这是以后要填进论文的真实地址。

## 3．找到上传入口

空仓库页面找到上传已有文件的入口，通常显示为 `uploading an existing file`。如果仓库已有内容，则在文件列表上方选择 `Add file` → `Upload files`。

在电脑文件管理器中打开第1步的本机文件夹。确认里面直接能看到README.md、code、data、models、md等，而不是又套了一层pgfs-graphene。

Linux按 `Ctrl+H` 显示隐藏文件，这样 `.gitignore`、`.gitattributes` 也能一起上传。

## 4．拖入文件并等待完成

1. 在pgfs-graphene文件夹内部全选其内容。
2. 将这些文件和子文件夹一起拖进GitHub上传区域，保留目录层次。不要把所有子目录中的文件平铺到根目录。
3. 等待上传列表显示完成。网络不稳定时可以按顶层目录分批上传，每批提交一次；根目录的说明文件也要上传。
4. 检查上传列表应包含 `data/reference_619.npz`、`evaluation/predictions.npz`、`models/trained/FrozenAB.nep` 等路径。

不要混入之后运行分析生成的reproduced、work、.venv或解压出来的源码文件夹。首次收到本精简包时没有这些额外目录。

## 5．提交保存

在页面底部的提交信息框填写：

`Add PGFS graphene data and code`

新建个人仓库可提交到默认分支。点击提交按钮，通常为 `Commit changes`；若界面显示 `Propose changes` 并让你创建新分支，则还需要合并相应Pull Request，默认分支才会显示文件。

上传仍在进行时不要关闭页面。提交完成后会返回仓库的文件列表。

## 6．核对传对了没有

- 首页可以直接显示README，而不是只有一个整包ZIP或一层外部pgfs-graphene文件夹。
- 可以进入data、models、md、code、software目录。
- md/cases.json、md/curves.npz和md/inputs.zip都存在。
- 用未登录的浏览器窗口仍能访问仓库。

完整性检查：点击 `Code` → `Download ZIP`，下载解压后，在解压后的仓库根目录运行：

```bash
python code/verify_files.py
```

看到PASS表示文件哈希及内部归档检查通过。如果你上传前修改了README或添加许可文件，先在本地运行 `python code/update_checksums.py`，再上传更新后的哈希清单。

## 7．把真实地址填进文章

例如：

```latex
The data and code that support the findings of this study are available
at \url{https://github.com/YOUR_GITHUB_USERNAME/pgfs-graphene}.
```

把YOUR_GITHUB_USERNAME换成真实用户名；如果仓库名称也改了，须一起替换。本包包含完整处理曲线及关键结构，不包含完整原始MD轨迹，文章与README不要声称公开了全部原始MD输出。

## 常见情况

- 提示文件太大：确认上传的是精简包内部内容，不是外层整包ZIP或原始dump.xyz。内部最大文件低于25 MiB。
- 提示文件太多：确认没有展开software的源码归档，也没有混入分析输出；也可以按顶层目录分批上传。
- 网页看不懂NPZ/ZIP/GZ：这是正常的二进制或归档文件，需要下载后用脚本读取，不是文件损坏。
- 旧完整版已经上传：网页再上传不会自动删除旧文件，需要另行同步删除远程旧内容。本教程新建空仓库的步骤不覆盖已有仓库。

官方说明（2026-11-10核对）：
- https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository
- https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository
