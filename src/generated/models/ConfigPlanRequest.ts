/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { VerifyCheck } from './VerifyCheck';
export type ConfigPlanRequest = {
    device_id: string;
    commands: Array<string>;
    verify?: Array<VerifyCheck>;
    save_on_success?: boolean;
    description?: (string | null);
};

