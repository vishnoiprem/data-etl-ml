#!/bin/bash
echo "Cleaning up large files..."
git filter-repo \
  --path venv/lib/python3.10/site-packages/tensorflow/libtensorflow_cc.2.dylib \
  --path venv/lib/python3.10/site-packages/torch/lib/libtorch_cpu.dylib \
  --path venv/lib/python3.10/site-packages/pyflink/lib/flink-dist-2.1.0.jar \
  --path *.safetensors \
  --strip-blobs-bigger-than 50M

git lfs untrack "*.safetensors"
git lfs untrack "*.pth"

rm -f .gitattributes
echo "Cleanup complete!"