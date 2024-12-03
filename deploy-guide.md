# Deploy with CI/CD systems and pipelines

Automatically generate deployment pipelines

Generate the required AWS infrastructure resources to connect to your CI/CD system. This step must be run for each deployment stage in your pipeline prior to running the sam pipeline init command.

Replace the `IAM_USER_ARN` to your IAM user ARN.

```bash
IAM_USER_ARN=arn:aws:iam::1234567890:user/username

# Generate resources for dev stage
sam pipeline bootstrap --no-interactive \
    --no-confirm-changeset \
    --region us-east-2 \
    --pipeline-user ${IAM_USER_ARN} \
    --config-env dev \
    --stage dev

# Generate resources for prod stage
sam pipeline bootstrap --no-interactive \
    --no-confirm-changeset \
    --region us-east-2 \
    --pipeline-user ${IAM_USER_ARN} \
    --config-env prod \
    --stage prod
```

Generate a pipeline configuration file that your CI/CD system can use to deploy serverless applications using AWS SAM.

We will use Github actions for CI/CD deployment.


```bash
sam pipeline init --save-params
```


```bash
Select a pipeline template to get started:
        1 - AWS Quick Start Pipeline Templates
        2 - Custom Pipeline Template Location
Choice: 1

Select CI/CD system
        1 - Jenkins
        2 - GitLab CI/CD
        3 - GitHub Actions
        4 - Bitbucket Pipelines
        5 - AWS CodePipeline
Choice: 3

What is the GitHub secret name for pipeline user account access key ID? [AWS_ACCESS_KEY_ID]: 
What is the GitHub Secret name for pipeline user account access key secret? [AWS_SECRET_ACCESS_KEY]: 
What is the git branch used for production deployments? [main]: 
What is the template file path? [template.yaml]: 

Here are the stage configuration names detected in .aws-sam/pipeline/pipelineconfig.toml:
        1 - dev
        2 - prod
Select an index or enter the stage 1's configuration name (as provided during the bootstrapping): 1
What is the sam application stack name for stage 1? [sam-app]: sam-app-dev
Stage 1 configured successfully, configuring stage 2.

Here are the stage configuration names detected in .aws-sam/pipeline/pipelineconfig.toml:
        1 - dev
        2 - prod
Select an index or enter the stage 2's configuration name (as provided during the bootstrapping): 2
What is the sam application stack name for stage 2? [sam-app]: sam-app-prod
Stage 2 configured successfully.
```

This will generate pipeline configuration in `.github/workflows/pipeline.yaml`


### Update pipeline for [RDS Proxy](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-proxy.html)

If you created your project with RDS Proxy, you need database user name and password.

You should add them in the GitHub secrets for CI/CD. Add `RDS_DATABASE_USERNAME` and `RDS_DATABASE_PASSWORD` secrets in your GitHub repository.

```bash
RDS_DATABASE_USERNAME=Your user name
RDS_DATABASE_PASSWORD=Your password
```


Open the `pipeline.yaml` and add following 
```bash
...
env:
  RDS_DATABASE_USERNAME: ${{ secrets.RDS_DATABASE_USERNAME }}
  RDS_DATABASE_PASSWORD: ${{ secrets.RDS_DATABASE_PASSWORD }}
...
```


Add parameter-overrides options to `sam deploy` commands. There are 3 deploy commands in the `pipeline.yaml` file.

```bash
sam deploy --stack-name ${PROD_STACK_NAME} \
--config-env prod \
--template packaged-prod.yaml \
--capabilities CAPABILITY_IAM \
--no-confirm-changeset \
--region ${PROD_REGION} \
--s3-bucket ${PROD_ARTIFACTS_BUCKET} \
--no-fail-on-empty-changeset \
--parameter-overrides DBUsername=${RDS_DATABASE_USERNAME} DBPassword=${RDS_DATABASE_PASSWORD} \
--role-arn ${PROD_CLOUDFORMATION_EXECUTION_ROLE}
```



## Initialize Git and Add Github repository

You will initialize git and add github repository. 


```bash
cd hello-world-app
git init
git add .
git commit -m 'initial commit'
git branch -m main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push origin main
```

GitHub Actions will deploy your SAM template to AWS on push main branch.