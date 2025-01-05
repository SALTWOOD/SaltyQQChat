from typing import Callable, Any
import re

class CommandBuilder:
    def __init__(self):
        self.commands: list[tuple[re.Pattern | str, list[type] | None, Callable]] = []

    def add_command(self, regex: re.Pattern | str, types: list[type] | None, func: Callable) -> bool:
        if not len([e for e in self.commands if e[0] == regex]):
            self.commands.append((regex, types, func))
            return True
        return False
    
    def remove_command(self, regex: re.Pattern | str) -> bool:
        commands = [c for c in self.commands if c[0] != regex]
        result = commands == self.commands
        self.commands = commands
        return result

    def handle(self, command: str) -> tuple[bool, Any | None]:
        func, params = self.get(command)
        if func is not None:
            return (True, func(*params))
        return (False, None)
    
    def _run(self, func: Callable, args: list[Any]) -> Any:
        return func(*args)

    def __call__(self, command: str) -> Callable | None:
        return self.handle(command)
    
    def get(self, command: str) -> tuple[Callable | None, Any | None]:
        for regex, types, func in self.commands:
            try:
                if isinstance(regex, re.Pattern):
                    match = regex.match(command)
                    if match is not None:
                        args = self.type_check(match.groups(), types)
                        return (func, args)
                    else: continue
                elif isinstance(regex, str) and regex == command:
                    return (func, None)
            except ValueError: ...
        return (None, None)
    
    def __repr__(self) -> str:
        command_count = len(self.commands)
        return f"<CommandBuilder commands: {command_count} command{'s' if command_count == 1 else ''}>"

    @staticmethod
    def type_check(input_list: list[str], target_types: list[type] | None) -> list[Any]:
        if target_types is None:
            if len(input_list) == 0:
                return []
            else:
                count = len(input_list)
                raise ValueError(f"This function takes no arguments but {count} were given.")
        
        result = []

        def try_convert(item, target_type):
            """尝试将 item 转换为 target_type"""
            try:
                if target_type == int:
                    return int(item)
                elif target_type == float:
                    return float(item)
                elif target_type == bool:
                    return bool(item)
                elif target_type == str:
                    return str(item)
                elif isinstance(target_type, type):  # 普通类型
                    return target_type(item)
                else:
                    # 针对用户自定义类型或复杂类型的转换处理
                    if hasattr(target_type, "__call__"):
                        # 如果 target_type 是可调用的（例如自定义类的构造函数）
                        return target_type(item)
                    else:
                        # 如果目标类型没有简单的构造函数，则尝试其他方法
                        raise ValueError(f"无法将 {item} 转换为 {target_type}")
            except Exception as e:
                raise ValueError(f"Failed to convert {item} to {target_type}: {e}")

        for item in input_list:
            # 遍历所有目标类型，尝试转换
            for target_type in target_types:
                converted_item = try_convert(item, target_type)
                if converted_item is not None:
                    result.append(converted_item)
                    break  # 成功转换后跳出循环，进入下一个元素
                else:
                    continue

        return result
    
if __name__ == '__main__':
    import sys
    
    builder = CommandBuilder()
    builder.add_command(re.compile(r'echo (.*)'), [str], lambda s: print(s))
    builder.add_command(re.compile(r'add (.*) (.*)'), [int, int], lambda a, b: int(a) + int(b))
    builder.add_command(re.compile(r'sub (.*) (.*)'), [int, int], lambda a, b: int(a) - int(b))
    builder.add_command(re.compile(r'mul (.*) (.*)'), [int, int], lambda a, b: int(a) * int(b))
    builder.add_command(re.compile(r'div (.*) (.*)'), [int, int], lambda a, b: int(a) / int(b))
    builder.add_command("exit", None, lambda: sys.exit())
    
    while True:
        command = input('> ')
        success, result = builder.handle(command)
        if success:
            print(result)
        else:
            print('Unknown command')