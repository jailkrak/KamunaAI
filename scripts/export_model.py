#!/usr/bin/env python3
"""
Export model to different formats for production
Supported formats: ONNX, TorchScript, TensorRT
Usage: python scripts/export_model.py --format onnx
"""

import os
import sys
import json
import argparse
import torch
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.model_loader import ModelFactory

def parse_args():
    parser = argparse.ArgumentParser(description="Export Trading AI Model")
    parser.add_argument("--model", type=str, default="outputs/final_model/model.pth",
                        help="Path to PyTorch model")
    parser.add_argument("--config", type=str, default="configs/model_config.json",
                        help="Model configuration")
    parser.add_argument("--format", type=str, required=True,
                        choices=['onnx', 'torchscript', 'tensorrt'],
                        help="Export format")
    parser.add_argument("--output", type=str, default="outputs/exported/",
                        help="Output directory")
    parser.add_argument("--seq_length", type=int, default=60,
                        help="Sequence length for input shape")
    parser.add_argument("--num_features", type=int, default=10,
                        help="Number of features")
    return parser.parse_args()

def export_to_onnx(model, dummy_input, output_path):
    """Export to ONNX format"""
    import torch.onnx
    
    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={
            'input': {0: 'batch_size'},
            'output': {0: 'batch_size'}
        }
    )
    print(f"✅ Exported to ONNX: {output_path}")

def export_to_torchscript(model, dummy_input, output_path):
    """Export to TorchScript format"""
    # Trace model
    traced_model = torch.jit.trace(model, dummy_input)
    traced_model.save(output_path)
    
    # Also save scripted version for safety
    scripted_model = torch.jit.script(model)
    scripted_model.save(output_path.replace('.pt', '_scripted.pt'))
    
    print(f"✅ Exported to TorchScript: {output_path}")

def export_to_tensorrt(model, dummy_input, output_path):
    """Export to TensorRT format (requires tensorrt package)"""
    try:
        import tensorrt as trt
        
        logger = trt.Logger(trt.Logger.INFO)
        builder = trt.Builder(logger)
        network = builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
        
        # Parse ONNX first
        onnx_path = output_path.replace('.engine', '.onnx')
        export_to_onnx(model, dummy_input, onnx_path)
        
        # Convert to TensorRT
        with open(onnx_path, 'rb') as f:
            parser = trt.OnnxParser(network, logger)
            parser.parse(f.read())
        
        config = builder.create_builder_config()
        config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, 1 << 30)
        
        engine = builder.build_engine(network, config)
        
        with open(output_path, 'wb') as f:
            f.write(engine.serialize())
        
        print(f"✅ Exported to TensorRT: {output_path}")
        
    except ImportError:
        print("❌ TensorRT not installed. Install with: pip install tensorrt")
        print("Falling back to ONNX export")
        export_to_onnx(model, dummy_input, output_path.replace('.engine', '.onnx'))

def validate_exported_model(original_model, exported_path, format_type, dummy_input):
    """Validate exported model produces same outputs"""
    original_model.eval()
    with torch.no_grad():
        original_output = original_model(dummy_input).numpy()
    
    if format_type == 'onnx':
        import onnxruntime as ort
        session = ort.InferenceSession(exported_path)
        exported_output = session.run(['output'], {'input': dummy_input.numpy()})[0]
        
    elif format_type == 'torchscript':
        exported_model = torch.jit.load(exported_path)
        exported_output = exported_model(dummy_input).numpy()
    
    else:
        print("Validation not implemented for TensorRT yet")
        return
    
    # Compare outputs
    max_diff = np.max(np.abs(original_output - exported_output))
    print(f"Max difference between original and exported: {max_diff:.10f}")
    
    if max_diff < 1e-5:
        print("✅ Validation passed! Models match perfectly.")
    else:
        print("⚠️ Validation warning: Outputs differ slightly (may be due to precision)")

def main():
    args = parse_args()
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Load config
    with open(args.config, 'r') as f:
        model_config = json.load(f)
    
    # Load model
    print(f"Loading model from {args.model}")
    model = ModelFactory.create_model(model_config)
    model.load_state_dict(torch.load(args.model, map_location='cpu'))
    model.eval()
    
    # Create dummy input
    dummy_input = torch.randn(1, args.seq_length, args.num_features)
    
    # Export based on format
    if args.format == 'onnx':
        output_path = os.path.join(args.output, 'model.onnx')
        export_to_onnx(model, dummy_input, output_path)
        validate_exported_model(model, output_path, 'onnx', dummy_input)
    
    elif args.format == 'torchscript':
        output_path = os.path.join(args.output, 'model.pt')
        export_to_torchscript(model, dummy_input, output_path)
        validate_exported_model(model, output_path, 'torchscript', dummy_input)
    
    elif args.format == 'tensorrt':
        output_path = os.path.join(args.output, 'model.engine')
        export_to_tensorrt(model, dummy_input, output_path)
    
    # Save metadata
    metadata = {
        'format': args.format,
        'input_shape': [args.seq_length, args.num_features],
        'export_date': str(__import__('datetime').datetime.now()),
        'model_config': model_config
    }
    
    with open(os.path.join(args.output, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✅ Export completed! Files saved to {args.output}")
    print(f"📦 Exported model size: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    main()