#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { execSync } from "node:child_process";

import { BackendEdgeStack } from "../lib/stacks/backend-edge-stack";
import { FrontendStack } from "../lib/stacks/frontend-stack";

const APP_NAME = "Aff";

function defaultEnvironment(): string {
  try {
    const user = process.env.USER || execSync("whoami").toString().trim();
    return `preview-${user}`;
  } catch {
    return "preview-local";
  }
}

const app = new cdk.App();
const environment = app.node.tryGetContext("environment") ?? defaultEnvironment();
const buildPath = app.node.tryGetContext("buildPath") ?? "../clients/app/dist";
const account = process.env.CDK_DEFAULT_ACCOUNT;
const region = process.env.CDK_DEFAULT_REGION || process.env.AWS_REGION || process.env.AWS_DEFAULT_REGION || "ap-southeast-1";

new BackendEdgeStack(app, `${APP_NAME}BackendEdge-${environment}`, {
  env: { account, region },
  environment,
  description: `HTTPS edge for backend origin - ${environment}`
});

new FrontendStack(app, `${APP_NAME}Frontend-${environment}`, {
  env: { account, region },
  environment,
  buildOutputPath: buildPath,
  description: `Static frontend hosting - ${environment}`
});

cdk.Tags.of(app).add("Project", APP_NAME);
cdk.Tags.of(app).add("ManagedBy", "CDK");
cdk.Tags.of(app).add("Environment", environment);
