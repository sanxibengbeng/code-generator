import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as autoscaling from 'aws-cdk-lib/aws-autoscaling';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as route53 from 'aws-cdk-lib/aws-route53';
import * as targets from 'aws-cdk-lib/aws-route53-targets';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import { RemovalPolicy } from 'aws-cdk-lib';

export class CodeGenStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create a unique identifier for this deployment
    const deploymentId = id.toLowerCase().replace(/[^a-z0-9]/g, '');

    // Create a VPC
    const vpc = new ec2.Vpc(this, 'CodeGenVPC', {
      maxAzs: 2,
      natGateways: 1,
      subnetConfiguration: [
        {
          cidrMask: 24,
          name: `${deploymentId}-public`,
          subnetType: ec2.SubnetType.PUBLIC,
        },
        {
          cidrMask: 24,
          name: `${deploymentId}-private`,
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
        }
      ],
      vpcName: `${deploymentId}-vpc`
    });
    
    // Add VPC Endpoints for SSM to connect to EC2 instances in private subnets
    new ec2.InterfaceVpcEndpoint(this, 'SSMEndpoint', {
      vpc,
      service: ec2.InterfaceVpcEndpointAwsService.SSM,
      privateDnsEnabled: true,
      subnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS }
    });
    
    new ec2.InterfaceVpcEndpoint(this, 'SSMMessagesEndpoint', {
      vpc,
      service: ec2.InterfaceVpcEndpointAwsService.SSM_MESSAGES,
      privateDnsEnabled: true,
      subnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS }
    });
    
    new ec2.InterfaceVpcEndpoint(this, 'EC2MessagesEndpoint', {
      vpc,
      service: ec2.InterfaceVpcEndpointAwsService.EC2_MESSAGES,
      privateDnsEnabled: true,
      subnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS }
    });

    // Create IAM role for EC2 instances with Bedrock permissions
    const ec2Role = new iam.Role(this, 'EC2Role', {
      assumedBy: new iam.ServicePrincipal('ec2.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonSSMManagedInstanceCore'),
      ],
      roleName: `${deploymentId}-ec2-role`,
      description: `EC2 role for ${deploymentId} deployment with Bedrock access`
    });

    // Add Bedrock permissions to the role
    const bedrockPolicy = new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock:InvokeModel',
        'bedrock:InvokeModelWithResponseStream',
        'bedrock:ListFoundationModels',
        'bedrock:GetFoundationModel',
      ],
      resources: ['*'], // You might want to restrict this to specific model ARNs in production
    });
    
    ec2Role.addToPolicy(bedrockPolicy);

    // Create security group for EC2 instances
    const appSecurityGroup = new ec2.SecurityGroup(this, 'AppSecurityGroup', {
      vpc,
      description: `Security group for ${deploymentId} Code Generator application`,
      allowAllOutbound: true,
      securityGroupName: `${deploymentId}-app-sg`
    });

    // Create security group for ALB
    const albSecurityGroup = new ec2.SecurityGroup(this, 'AlbSecurityGroup', {
      vpc,
      description: `Security group for ${deploymentId} Application Load Balancer`,
      allowAllOutbound: true,
      securityGroupName: `${deploymentId}-alb-sg`
    });

    // Allow HTTP traffic from ALB to EC2 instances
    appSecurityGroup.addIngressRule(
      albSecurityGroup,
      ec2.Port.tcp(8080),
      'Allow HTTP traffic from ALB'
    );

    // Allow HTTPS and HTTP traffic to ALB
    albSecurityGroup.addIngressRule(
      ec2.Peer.anyIpv4(),
      ec2.Port.tcp(443),
      'Allow HTTPS traffic from internet'
    );
    
    albSecurityGroup.addIngressRule(
      ec2.Peer.anyIpv4(),
      ec2.Port.tcp(80),
      'Allow HTTP traffic from internet'
    );

    // Create user data for EC2 instances
    const userData = ec2.UserData.forLinux();
    userData.addCommands(
      '#!/bin/bash',
      'exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1',
      'echo "Starting user data script execution"',
      'yum update -y',
      'yum install -y git python3 python3-pip make',
      'pip3 install --upgrade pip',
      'echo "Cloning repository..."',
      'cd /home/ec2-user',
      'git clone https://github.com/sanxibengbeng/code-generator.git',
      'if [ $? -ne 0 ]; then',
      '  echo "Git clone failed, retrying..."',
      '  sleep 5',
      '  git clone https://github.com/sanxibengbeng/code-generator.git',
      'fi',
      'echo "Setting up application directory..."',
      'cd code-generator/src',
      'mkdir -p uploads',
      'chown -R ec2-user:ec2-user /home/ec2-user/code-generator',
      'chmod 755 uploads',
      'echo "Running make env..."',
      'sudo -u ec2-user make env',
      'echo "Setting up service..."',
      'chmod +x /home/ec2-user/code-generator/src/start_app.sh',
      'echo "#!/bin/bash" > /home/ec2-user/code-generator/src/start_app.sh',
      'echo "cd /home/ec2-user/code-generator/src" >> /home/ec2-user/code-generator/src/start_app.sh',
      'echo "source venv/bin/activate" >> /home/ec2-user/code-generator/src/start_app.sh',
      'echo "python app.py" >> /home/ec2-user/code-generator/src/start_app.sh',
      'chmod +x /home/ec2-user/code-generator/src/start_app.sh',
      'echo "[Unit]" > /etc/systemd/system/codegen.service',
      'echo "Description=Code Generator Flask Application" >> /etc/systemd/system/codegen.service',
      'echo "After=network.target" >> /etc/systemd/system/codegen.service',
      'echo "" >> /etc/systemd/system/codegen.service',
      'echo "[Service]" >> /etc/systemd/system/codegen.service',
      'echo "User=ec2-user" >> /etc/systemd/system/codegen.service',
      'echo "WorkingDirectory=/home/ec2-user/code-generator/src" >> /etc/systemd/system/codegen.service',
      'echo "ExecStart=/home/ec2-user/code-generator/src/start_app.sh" >> /etc/systemd/system/codegen.service',
      'echo "Restart=always" >> /etc/systemd/system/codegen.service',
      'echo "" >> /etc/systemd/system/codegen.service',
      'echo "[Install]" >> /etc/systemd/system/codegen.service',
      'echo "WantedBy=multi-user.target" >> /etc/systemd/system/codegen.service',
      'systemctl daemon-reload',
      'systemctl enable codegen.service',
      'systemctl start codegen.service'
    );

    // Create launch template
    const launchTemplate = new ec2.LaunchTemplate(this, 'CodeGenLaunchTemplate', {
      machineImage: ec2.MachineImage.latestAmazonLinux2023({
        cpuType: ec2.AmazonLinuxCpuType.ARM_64 // Specify ARM architecture for T4g
      }),
      instanceType: ec2.InstanceType.of(ec2.InstanceClass.T4G, ec2.InstanceSize.MEDIUM),
      securityGroup: appSecurityGroup,
      userData,
      role: ec2Role,
      blockDevices: [
        {
          deviceName: '/dev/xvda',
          volume: ec2.BlockDeviceVolume.ebs(20, {
            volumeType: ec2.EbsDeviceVolumeType.GP3,
            encrypted: true,
          }),
        },
      ],
      launchTemplateName: `${deploymentId}-launch-template`,
    });

    // Create Auto Scaling Group
    const asg = new autoscaling.AutoScalingGroup(this, 'CodeGenASG', {
      vpc,
      launchTemplate,
      minCapacity: 1,
      maxCapacity: 3,
      desiredCapacity: 1,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      healthCheck: autoscaling.HealthCheck.elb({
        grace: cdk.Duration.minutes(5),
      }),
      autoScalingGroupName: `${deploymentId}-asg`,
      // Configure blue/green deployment options
      updatePolicy: autoscaling.UpdatePolicy.rollingUpdate({
        maxBatchSize: 1,
        minInstancesInService: 1,
        pauseTime: cdk.Duration.minutes(5),
        waitOnResourceSignals: true,
        suspendProcesses: [
          autoscaling.ScalingProcess.ALARM_NOTIFICATION,
          autoscaling.ScalingProcess.SCHEDULED_ACTIONS
        ]
      })
    });

    // Create Application Load Balancer
    const alb = new elbv2.ApplicationLoadBalancer(this, 'CodeGenALB', {
      vpc,
      internetFacing: true,
      securityGroup: albSecurityGroup,
      vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC },
      loadBalancerName: `${deploymentId}-alb`,
    });

    // Create HTTP listener
    const httpListener = alb.addListener(`${deploymentId}-HttpListener`, {
      port: 80,
      protocol: elbv2.ApplicationProtocol.HTTP,
      defaultAction: elbv2.ListenerAction.fixedResponse(200, {
        contentType: 'text/html',
        messageBody: '<html><body><h1>Hello from Code Generator!</h1></body></html>',
      }),
    });

    // Add target group to HTTP listener
    const targetGroup = httpListener.addTargets(`${deploymentId}-TargetGroup`, {
      port: 8080,
      protocol: elbv2.ApplicationProtocol.HTTP,
      targets: [asg],
      healthCheck: {
        path: '/',
        interval: cdk.Duration.seconds(30),
        timeout: cdk.Duration.seconds(5),
        healthyThresholdCount: 2,
        unhealthyThresholdCount: 5,
      },
      deregistrationDelay: cdk.Duration.seconds(30),
      targetGroupName: `${deploymentId}-tg`,
    });

    // Output the ALB DNS name
    new cdk.CfnOutput(this, `${deploymentId}-AlbDnsName`, {
      value: alb.loadBalancerDnsName,
      description: `The DNS name of the ${deploymentId} load balancer`,
      exportName: `${deploymentId}-AlbDnsName`,
    });
    
    // Create CloudFront distribution
    const distribution = new cloudfront.Distribution(this, 'CloudFrontDistribution', {
      defaultBehavior: {
        origin: new origins.LoadBalancerV2Origin(alb, {
          protocolPolicy: cloudfront.OriginProtocolPolicy.HTTP_ONLY,
        }),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
        cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
        originRequestPolicy: cloudfront.OriginRequestPolicy.ALL_VIEWER,
      },
      priceClass: cloudfront.PriceClass.PRICE_CLASS_100, // Use only North America and Europe
      enabled: true,
      comment: `CloudFront distribution for ${deploymentId} Code Generator`,
      defaultRootObject: '/',
      enableLogging: true,
    });
    
    // Output the CloudFront distribution domain name
    new cdk.CfnOutput(this, `${deploymentId}-CloudFrontDomain`, {
      value: distribution.distributionDomainName,
      description: `The domain name of the ${deploymentId} CloudFront distribution`,
      exportName: `${deploymentId}-CloudFrontDomain`,
    });
    
    // Add tags to all resources
    cdk.Tags.of(this).add('Project', 'CodeGenerator');
    cdk.Tags.of(this).add('DeploymentId', deploymentId);
    cdk.Tags.of(this).add('Environment', props?.env?.account || 'development');
  }
}
