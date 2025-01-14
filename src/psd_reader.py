from psd_tools import PSDImage
import os
import json
from PIL import Image
import logging
from pathlib import Path

class PsdReader:
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.config = {}
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    async def process_all_psd_files(self):
        """处理输入目录中的所有PSD文件"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        for file in self.input_dir.glob('*.psd'):
            self.logger.info(f"Processing {file.name}")
            await self.process_psd_file(file.name)
        
        await self.save_config()

    async def process_psd_file(self, filename: str):
        """处理单个PSD文件"""
        psd = PSDImage.open(self.input_dir / filename)
        self.traverse_layers(psd, filename)

    def sanitize_name(self, name: str) -> str:
        """清理文件名中的非法字符"""
        # 替换Windows文件系统中的非法字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name

    def sanitize_path(self, path: str) -> Path:
        """清理路径中的非法字符"""
        parts = Path(path).parts
        sanitized_parts = [self.sanitize_name(part) for part in parts]
        return Path(*sanitized_parts)

    def traverse_layers(self, psd, psd_name: str, parent_path: str = ''):
        """递归遍历PSD中的所有图层"""
        for layer in psd:
            if layer.is_group():
                new_parent = str(Path(parent_path) / self.sanitize_name(layer.name))
                self.traverse_layers(layer, psd_name, new_parent)
            else:
                self.export_layer(layer, psd_name, parent_path)

    def export_layer(self, layer, psd_name: str, parent_path: str):
        """导出单个图层"""
        if not layer.visible:
            return

        try:
            # 创建扁平化的文件名
            layer_path = parent_path.replace(os.sep, '_') if parent_path else ''
            layer_name = self.sanitize_name(layer.name)
            if layer_path:
                filename = f"{layer_path}_{layer_name}.png"
            else:
                filename = f"{layer_name}.png"

            # 确保输出目录存在
            output_dir = os.path.abspath(self.output_dir)
            os.makedirs(output_dir, exist_ok=True)

            # 导出图层为PNG
            layer_image = layer.composite()
            if layer_image:
                full_path = os.path.join(output_dir, filename)
                self.logger.info(f"Saving layer to: {full_path}")
                
                # 使用二进制模式打开文件
                with open(full_path, 'wb') as f:
                    layer_image.save(f, format='PNG')

                # 保存图层信息
                self.save_layer_config(layer, psd_name, layer_path, filename)
        except Exception as e:
            self.logger.error(f"Error exporting layer {layer.name}: {str(e)}")
            raise

    def save_layer_config(self, layer, psd_name: str, parent_path: str, filename: str):
        """保存图层信息到配置文件"""
        layer_info = {
            'name': layer.name,
            'path': str(Path(parent_path) / filename),
            'width': layer.width,
            'height': layer.height,
            'position': {'x': layer.left, 'y': layer.top},
            'opacity': layer.opacity,
            'visible': layer.visible,
            'psd_source': psd_name,
            'blend_mode': str(layer.blend_mode),
            'layer_type': layer.__class__.__name__
        }

        if psd_name not in self.config:
            self.config[psd_name] = []
        self.config[psd_name].append(layer_info)

    async def save_config(self):
        """保存配置到JSON文件"""
        config_path = self.output_dir / 'config.json'
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2) 