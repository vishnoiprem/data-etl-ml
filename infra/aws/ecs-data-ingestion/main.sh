sudo yum -y update
sudo yum install -y docker
sudo service docker start

aws configure


wget https://github.com/Educative-Content/my-ecs-demo-app-v2/zipball/master/main.zip &&\
unzip main.zip &&\
cd Educative-Content-my-ecs-demo-app-v2-b6a55fd



ACCOUNT_ID="777307045838" &&\
aws ecr get-login-password --region us-east-1 | sudo docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com


sudo docker build -t ecs-container-repo .

sudo docker tag ecs-container-repo:latest $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ecs-container-repo:latest



sudo docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ecs-container-repo:latest

