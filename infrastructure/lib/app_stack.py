from aws_cdk import CfnOutput, Duration, Stack
from aws_cdk.aws_bedrock_agentcore_alpha import Runtime, AgentRuntimeArtifact
from aws_cdk.aws_iam import Role, PolicyStatement, ManagedPolicy, ServicePrincipal
from aws_cdk.aws_ecr_assets import Platform
from aws_cdk.aws_lambda import Function, Runtime as LambdaRuntime, Code
from aws_cdk.aws_apigateway import RestApi, LambdaIntegration, Cors, CorsOptions
from constructs import Construct

class AppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, app_name: str, env_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        APP_NAME = app_name
        ENV_NAME = env_name

        #
        # Amazon Bedrock AgentCore
        #

        role = Role(self, "AgentRole",
            assumed_by=ServicePrincipal("bedrock-agentcore.amazonaws.com"),
            managed_policies=[
                ManagedPolicy.from_aws_managed_policy_name("CloudWatchFullAccess"),
            ]
        )

        role.add_to_policy(PolicyStatement(
            actions=["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
            resources=["*"]
        ))

        teddieai_agent_runtime_artifact = AgentRuntimeArtifact.from_asset(
            directory="../backend/teddieai",
            platform=Platform.LINUX_ARM64
        )

        teddieai_runtime = Runtime(self, "TeddieAIAgentRuntime",
            runtime_name=f"{APP_NAME}_teddieai_{ENV_NAME}".replace("-", "_"),
            execution_role=role,
            agent_runtime_artifact= teddieai_agent_runtime_artifact,
        )

        membrane_agent_runtime_artifact = AgentRuntimeArtifact.from_asset(
            directory="../backend/membrane",
            platform=Platform.LINUX_ARM64
        )

        membrane_runtime = Runtime(self, "MembraneAgentRuntime",
            runtime_name=f"{APP_NAME}_membrane_{ENV_NAME}".replace("-", "_"),
            execution_role=role,
            agent_runtime_artifact=membrane_agent_runtime_artifact,
        )

        #
        # Invoker Lambdas
        #
        
        teddie_invoker = Function(self, "TeddieAIInvoker",
            runtime=LambdaRuntime.PYTHON_3_12,
            handler="index.handler",
            code=Code.from_asset("../backend/invoker"),
            environment={
                "AGENT_RUNTIME_ARN": teddieai_runtime.agent_runtime_arn
            },
            timeout=Duration.seconds(60),
            # role=role  <-- Removed incorrect role sharing. CDK will create a role trusting lambda.
        )
        
        # Grant invoke permissions to the Lambda
        teddie_invoker.add_to_role_policy(PolicyStatement(
            actions=["bedrock-agentcore:InvokeAgentRuntime"],
            resources=[teddieai_runtime.agent_runtime_arn, f"{teddieai_runtime.agent_runtime_arn}/*"]
        ))

        membrane_invoker = Function(self, "MembraneInvoker",
            runtime=LambdaRuntime.PYTHON_3_12,
            handler="index.handler",
            code=Code.from_asset("../backend/invoker"),
            environment={
                "AGENT_RUNTIME_ARN": membrane_runtime.agent_runtime_arn
            },
            timeout=Duration.seconds(60),
        )
        
        membrane_invoker.add_to_role_policy(PolicyStatement(
            actions=["bedrock-agentcore:InvokeAgentRuntime"],
            resources=[membrane_runtime.agent_runtime_arn, f"{membrane_runtime.agent_runtime_arn}/*"]
        ))

        #
        # API Gateway
        #

        api = RestApi(self, "AgentCoreApi",
            rest_api_name=f"{APP_NAME}-agent-api-{ENV_NAME}",
            default_cors_preflight_options=CorsOptions(
                allow_origins=Cors.ALL_ORIGINS,
                allow_methods=Cors.ALL_METHODS
            )
        )

        teddie_resource = api.root.add_resource("teddieai")
        teddie_resource.add_method("POST", LambdaIntegration(teddie_invoker))

        membrane_resource = api.root.add_resource("membrane")
        membrane_resource.add_method("POST", LambdaIntegration(membrane_invoker))

        CfnOutput(self, "ApiUrl", value=api.url)