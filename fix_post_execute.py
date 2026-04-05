import re

with open('main.py', 'r') as f:
    content = f.read()

# Find post_execute
start_idx = content.find('async def post_execute(request):')
if start_idx != -1:
    # Find the start of def run_task_thread(): inside post_execute
    run_task_idx = content.find('    def run_task_thread():', start_idx)
    if run_task_idx != -1:
        # Find the end of thread.start()
        thread_start_idx = content.find('    thread.start()', run_task_idx)
        if thread_start_idx != -1:
            end_idx = thread_start_idx + len('    thread.start()')
            
            # Replace the whole block with start_execution_thread
            new_block = '    start_execution_thread(exec_id, prompt, model, workspace, mcp_config, loop, q, in_q)'
            content = content[:run_task_idx] + new_block + content[end_idx:]

with open('main.py', 'w') as f:
    f.write(content)

