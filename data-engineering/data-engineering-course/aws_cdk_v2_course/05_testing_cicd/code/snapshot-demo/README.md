# snapshot-demo — L23 demo

This is a **demo snippet**, not a standalone project. It shows the
snapshot-test style for the `HelloCdkStack` from L22/L23.

To try it:

```bash
# from the course root
cp 05_testing_cicd/code/snapshot-demo/hello-cdk.snapshot.test.ts \
   02_app_stack_construct/code/hello-cdk/test/

cd 02_app_stack_construct/code/hello-cdk
npm test                                    # 5 + 1 tests now
ls test/__snapshots__/                      # new .snap file
```

The first run creates `__snapshots__/hello-cdk.snapshot.test.ts.snap`.
The second run compares; pass the `-u` flag to update.
