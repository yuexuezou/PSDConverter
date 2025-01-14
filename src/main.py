import asyncio
import os
from psd_reader import PsdReader

async def main():
    input_dir = os.path.join(os.path.dirname(__file__), '..', 'input')
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    
    reader = PsdReader(input_dir, output_dir)
    await reader.process_all_psd_files()

if __name__ == "__main__":
    asyncio.run(main()) 