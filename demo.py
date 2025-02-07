import re
from typing import Dict, List, Callable, Tuple
from dataclasses import dataclass
import time

@dataclass
class MemoryInfo:
    is_success: bool


class FunctionRegistry:
    """函数注册器，用于管理可调用的函数"""
    def __init__(self):
        self._functions: Dict[str, Callable] = {}
        self._descriptions: Dict[str, dict] = {}  # 存储函数的详细描述
    
    def register(self, name: str, func: Callable, description: str = None, parameters: Dict[str, dict] = None):
        """注册函数，同时记录其描述和参数信息"""
        self._functions[name] = func
        self._descriptions[name] = {
            "description": description or func.__doc__ or "No description available",
            "parameters": parameters or {}
        }
    
    def call(self, name: str, **kwargs):
        """调用已注册的函数"""
        if name not in self._functions:
            raise ValueError(f"Function '{name}' not found in registry")
        return self._functions[name](**kwargs)
    
    def generate_xml(self) -> str:
        """生成XML格式的函数描述"""
        xml_parts = []
        
        for name, info in self._descriptions.items():
            function_xml = [f'      <function name="{name}">']
            function_xml.append(f'        <description>{info["description"]}</description>')
            
            if info["parameters"]:
                for param_name, param_info in info["parameters"].items():
                    param_xml = [f'          <parameter name="{param_name}" type="{param_info["type"]}">']
                    param_xml.append(f'            <description>{param_info["description"]}</description>')
                    
                    if "options" in param_info:
                        param_xml.append('            <options>')
                        for option in param_info["options"]:
                            option_xml = [f'              <option value="{option["value"]}">']
                            option_xml.append(f'                <description>{option["description"]}</description>')
                            if "usage" in option:
                                option_xml.append(f'                <usage>{option["usage"]}</usage>')
                            option_xml.append('              </option>')
                        param_xml.append('\n'.join(option_xml))
                        param_xml.append('            </options>')
                    
                    param_xml.append('          </parameter>')
                    function_xml.append('\n'.join(param_xml))
            
            function_xml.append('      </function>')
            xml_parts.append('\n'.join(function_xml))
        
        return '\n'.join(xml_parts)    
    def update_system_prompt(self, system_prompt: str) -> str:
        """更新system_prompt中的functions部分"""
        import re
        
        # 生成新的functions内容
        new_functions = self.generate_xml()
        #print(new_functions)
        updated_prompt = re.sub(r'<function_system>.*?</function_system>', f"""<function_system>\n      <rule>请在请求函数调用后立即停止回复，等待函数调用</rule>\n{new_functions}\n    <function_rules>
      <rule>使用XML格式调用函数</rule>
      <rule>调用前告知用户</rule>
      <rule>等待函数响应后继续</rule>
      <example>
        <function_calls>
          <invoke name="function_name">
            <parameter name="param_name">param_value</parameter>
          </invoke>
        </function_calls>
      </example>
    </function_rules>\n</function_system>""", system_prompt, flags=re.DOTALL)
    #    return new_functions
        current_time = time.strftime("%Y-%m-%d %H:%M")
        updated_prompt = re.sub(r'<current_time>.*?</current_time>', f'<current_time>{current_time}</current_time>', updated_prompt, flags=re.DOTALL)
        return updated_prompt
    
def read_system_prompt():
    try:
        with open('system_prompt.xml', 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"读取system_prompt.xml时出错: {str(e)}")
        return None


def create_memory(content: str, priority: str):
    """创建新的记忆"""
    print(f"创建新的记忆：{content}，优先级：{priority}")
    #raise ValueError("创建记忆失败")
    return MemoryInfo(is_success=True)

def delete_memory(content: str, reason: str):
    """删除记忆"""
    print(f"删除记忆：{content},原因:{reason}")


def parse_and_execute_function_calls(xml_content: str, registry: FunctionRegistry) -> List[Dict]:
    """解析XML格式的function calls并执行函数"""
    results = []
    
    function_blocks = re.findall(
        r'<function_calls>(.*?)</function_calls>',
        xml_content,
        re.DOTALL
    )
    
    for block in function_blocks:
        invokes = re.findall(
            r'<invoke name="(.*?)">(.*?)</invoke>',
            block,
            re.DOTALL
        )
        
        for func_name, params in invokes:
            parameters = {}
            param_matches = re.findall(
                r'<parameter name="(.*?)">(.*?)</parameter>',
                params,
                re.DOTALL
            )
            
            for param_name, param_value in param_matches:
                parameters[param_name] = param_value.strip()
            
            # 执行函数调用
            try:
                result = registry.call(func_name, **parameters)
                results.append({
                    "function": func_name,
                    "parameters": parameters,
                    "result": result
                })
            except Exception as e:
                results.append({
                    "function": func_name,
                    "parameters": parameters,
                    "error": str(e)
                })
    
    return results

if __name__ == "__main__": 
    # 创建注册器
    registry = FunctionRegistry()
    
    # 注册create_memory函数
    registry.register(
        "create_memory",
        create_memory,  # 你的函数实现
        "创建新的记忆",
        {
            "content": {
                "type": "string",
                "description": "要存储的内容"
            },
            "priority": {
                "type": "string",
                "description": "记忆优先级：core/long/short",
                "options": [
                    {
                        "value": "core",
                        "description": "核心记忆，永久保存",
                        "usage": "重要约定、关键事件、深度交流"
                    },
                    {
                        "value": "long",
                        "description": "长期记忆",
                        "usage": "日常互动、习惯偏好"
                    },
                    {
                        "value": "short",
                        "description": "短期记忆",
                        "usage": "一般对话、临时信息"
                    }
                ]
            }
        }
    )
    # 注册delete_memory函数
    registry.register(
        "delete_memory",
        delete_memory,  
        "删除记忆",
        {
            "content": {
                "type": "string",
                "description": "要删除的内容"
            },
            "reason": {
                "type": "string",
                "description": "删除原因"
            }
        }
    )

    # 更新system_prompt
    system_prompt = read_system_prompt()
    
    updated_prompt = registry.update_system_prompt(system_prompt)

    test_xml = """
*点点头* 好的主人，我这就帮你添加这条测试
记忆~\n\n<function_calls>\n  <invoke name="create_memory">\n    <parameter name="content">主人进行了系统测试</parameter>\n    <parameter name="priority">short</parameter>\n  </invoke>\n</function_calls>\n\n*歪着头看着主人* 我已经把这条 记忆添加到短期记忆中啦！因为是测试用的记忆，所以我把它设为 了短期记忆优先级。主人还想测试什么功能吗？*眨眨眼睛*
"""

    results = parse_and_execute_function_calls(test_xml, registry)
    print(results)
