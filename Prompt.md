claude3.7 sonnet 写代码的demo：
1. prompt：选择合适的框架实现图片中的网页功能，要把html js css放在一个文件里面 ，要求自适应

Q DEV CLI 的demo

1. 结合AWS的bedrock 能力，调用美东1区的anthropic 3.7 sonnet 实现一个基于图片生成网页的工具；
2. 希望有一个html页面接受图片选择，并且展示处理进度；
3. 模型写出来的代码直接写入本地文件中；
4. 你可以考虑利用LLM tool use实现比如 创建一个保存文件的tool 
5. 尽量整合agentic的思路，可以自主规划代码生成的过程；
6. python 实现


当前项目是一个用python实现的flask站点,站点主要的代码在src目录下，入口函数是app.py。研究这个项目的代码，并利用cdk将其部署到AWS。实现如下功能：
1. 实现CDK 部署代码，放到cdk目录下；
2. 项目代码部署到一个EC2上，给EC2合适的权限以调用Bedrock 所有模型的推理能力；
3. 通过如下路径对外暴露服务  alb -> asg ->ec2, asg里面默认1台ec2

 结合AWS 架构图规范，根据cdk中的资源配置绘制draw.io 架构图，利用draw.io中的AWS官方图标库