import { z } from "zod";
import { SchemaVersionSchema } from "./common.js";

export const TestDataVariableTypeSchema = z.enum([
  "secret",
  "testData",
  "generated",
  "file"
]);
export type TestDataVariableType = z.infer<typeof TestDataVariableTypeSchema>;

export const SecretValueSourceSchema = z.enum([
  "localCredentialStore",
  "osKeychain",
  "envVar",
  "userInput",
  "literal"
]);

// Base variable shape used for refinement
const TestDataVariableBaseSchema = z
  .object({
    name: z.string().regex(/^[A-Z][A-Z0-9_]*$/),
    type: TestDataVariableTypeSchema,
    valueSource: SecretValueSourceSchema.optional(),
    value: z.string().optional(),
    pattern: z.string().optional(),
    filePath: z.string().optional(),
    sendToLlm: z.boolean(),
    description: z.string().optional()
  })
  .strict();

export const TestDataVariableSchema = TestDataVariableBaseSchema.superRefine(
  (data, ctx) => {
    if (data.type === "secret") {
      if (!data.valueSource) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "secret 타입은 valueSource 필수"
        });
      }
      if (data.sendToLlm !== false) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "secret 타입은 sendToLlm=false 필수"
        });
      }
      if (data.value !== undefined) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "secret 타입은 value 필드 사용 금지"
        });
      }
    }
    if (data.type === "testData" && data.value === undefined) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "testData 타입은 value 필수"
      });
    }
    if (data.type === "generated" && data.pattern === undefined) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "generated 타입은 pattern 필수"
      });
    }
    if (data.type === "file" && data.filePath === undefined) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "file 타입은 filePath 필수"
      });
    }
  }
);
export type TestDataVariable = z.infer<typeof TestDataVariableSchema>;

export const TestDataProfileSchema = z
  .object({
    schemaVersion: SchemaVersionSchema,
    testDataProfileId: z.string().min(1),
    name: z.string().min(1),
    description: z.string().optional(),
    variables: z.array(TestDataVariableSchema)
  })
  .strict();
export type TestDataProfile = z.infer<typeof TestDataProfileSchema>;
