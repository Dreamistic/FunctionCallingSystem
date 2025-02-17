# Function Calling Is All you need

## Intro

你还在为LLM只能依靠自身信息回复你吗？你还在为...省略1w种方式，今天，在下向您推出并非全新的FC功能，让您的AI也能实现实时联网，删改记忆，发送邮件，操控家里的电子设备！

简单来说，Function Calling是一个指定格式的文本，告诉后端该如何处理，同时将函数调用结果作为下一次LLM生成的prompt的一部分，目前最为热门的是Claude的[MCP项目](https://github.com/modelcontextprotocol/servers "github链接")，本人在构建这样一个系统中也踩过不少的坑，这个Function Calling系统经过三次重构，但仍然可能存在问题。

> 注：本文及所有代码均由**文心一言**生成，如有任何错误及bug请友好地咨询[文心一言](https://yiyan.baidu.com/ "官网地址 What's the problem with you")。

## 简介

这是一个基于XML格式的Function Calling系统，**主要用于实现AI助手调用外部函数的功能**。系统采用注册器模式设计，具有以下特点：

- 💡 **清晰的XML通信格式**：便于解析和验证
- 🔒 **安全的函数调用机制**：通过注册器管理函数访问
- 🔄 **完整的对话-执行-反馈循环**：支持复杂的交互场景
- ⚡ **灵活的扩展性**：易于添加新的函数和功能

## 核心组件

### 1. FunctionRegistry 类

这是整个系统的核心组件，负责管理和执行函数调用。

```python
class FunctionRegistry:
    def __init__(self):
        self._functions: Dict[str, Callable] = {}
        self._descriptions: Dict[str, dict] = {}

    def register(self, name: str, func: Callable, description: str = None, 
                parameters: Dict[str, dict] = None):
        """注册函数到注册器"""
        self._functions[name] = func
        self._descriptions[name] = {
            "description": description or func.__doc__ or "No description available",
            "parameters": parameters or {}
        }
```

### 2. 函数调用流程

以下是整个系统的核心工作流程：

```python
def process_conversation_turn(system_prompt: str, registry: FunctionRegistry, 
                            depth: int = 0) -> str:
    # 1. 获取AI响应
    response_content, has_function_calls = get_ai_response(system_prompt)
    
    # 2. 检查是否需要函数调用
    if has_function_calls:
        # 3. 解析并执行函数调用
        results = parse_and_execute_function_calls(response_content, registry)
        
        # 4. 处理函数调用结果
        if results:
            function_responses = []
            for result in results:
                # 处理结果...
                
            # 5. 更新对话上下文
            context.extend([
                {"role": "assistant", "content": 
                 f"<function_response>{function_responses}</function_response>"}
            ])
            
            # 6. 递归继续对话
            return process_conversation_turn(system_prompt, registry, depth + 1)
    
    return response_content
```

> 该函数为递归函数，若存在函数调用 has_function_call则会执行函数并进行下一次递归

## XML 通信格式

系统使用XML格式进行函数调用，格式示例，这也是AI到时候调用的格式：

```xml
<function_calls>
    <invoke name="create_memory">
        <parameter name="content">content</parameter>
        <parameter name="priority">core</parameter>
    </invoke>
</function_calls>
```

### 函数调用解析

系统使用正则表达式解析XML格式的函数调用：

```python
def parse_and_execute_function_calls(xml_content: str, registry: FunctionRegistry) -> List[Dict]:
    # 1. 解析function_calls块
    function_blocks = re.findall(
        r'<function_calls>(.*?)</function_calls>',
        xml_content,
        re.DOTALL
    )
    
    # 2. 解析每个invoke
    for block in function_blocks:
        invokes = re.findall(
            r'<invoke name="(.*?)">(.*?)</invoke>',
            block,
            re.DOTALL
        )
```

## 错误处理机制

系统实现了多层错误处理：

1. **函数执行错误**：通过 try-except 捕获并返回错误信息
2. **递归深度限制**：通过 MAX_DEPTH 控制对话深度
3. **结果格式化**：统一的XML响应格式

```python
def return_result_xml(content: str, success: bool) -> str:
    """返回统一格式的函数调用结果"""
    tag = "success" if success else "failed"
    return f"<{tag}>{content}</{tag}>"
```

## 使用示例

1. **注册函数**：

```python
registry = FunctionRegistry()
registry.register(
    "create_memory",
    create_memory,  
    "创建新的记忆",
    {
        "content": {
            "type": "string",
            "description": "要存储的内容"
        },
        "priority": {
            "type": "string",
            "description": "记忆优先级：core/long/short"
        }
    }
)
```

2. **运行对话**：

```python
def run_conversation(system_prompt: str):
    registry = FunctionRegistry()
    # 注册函数...
    return process_conversation_turn(system_prompt, registry, 0)
```
## 注意事项

- 🔔 每个函数调用都会更新对话上下文
- ⚠️ 需要注意递归深度限制(我这里默认5，防止某些模型无限循环)
- 📝 函数描述和参数信息要尽可能详细
- 🔄 确保XML格式的正确性
