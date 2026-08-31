"""util/tot_log_stream.py 模块单元测试。"""

from __future__ import annotations

import json
import threading

import pytest

from casevo.util.tot_log_stream import TotLogStream


@pytest.fixture
def initialized_log(tmp_path):
    """初始化独立日志目录，并在测试结束后清理订阅者。"""
    TotLogStream.init_log(2, str(tmp_path), buffer_size=10000, clear_old=True)
    yield tmp_path
    with TotLogStream._subscribers_lock:
        subscriber_ids = [item['sub_id'] for item in TotLogStream._subscribers]
    for subscriber_id in subscriber_ids:
        TotLogStream.unsubscribe(subscriber_id)


def test_subscribe_receives_complete_events(initialized_log):
    """订阅后应收到字段完整且 owner 正确的模型与代理事件。"""
    events = []
    subscription_id = TotLogStream.subscribe(events.append)

    TotLogStream.add_model_log(1, 'thought', {'value': 'model'})
    TotLogStream.add_agent_log(2, 'action', {'value': 'agent'}, 0)

    assert TotLogStream.unsubscribe(subscription_id)
    assert events == [
        {'ts': 1, 'owner': 'model', 'type': 'thought', 'item': {'value': 'model'}},
        {'ts': 2, 'owner': 'agent_0', 'type': 'action', 'item': {'value': 'agent'}},
    ]


def test_subscribe_owner_and_type_filters(initialized_log):
    """owner 和 type 过滤条件应只匹配对应事件。"""
    model_events = []
    action_events = []
    model_id = TotLogStream.subscribe(model_events.append, owner='model')
    action_id = TotLogStream.subscribe(action_events.append, type='action')

    TotLogStream.add_model_log(1, 'thought', 'm')
    TotLogStream.add_agent_log(2, 'action', 'a', 0)
    TotLogStream.add_agent_log(3, 'thought', 'a2', 0)

    assert len(model_events) == 1
    assert model_events[0]['owner'] == 'model'
    assert len(action_events) == 1
    assert action_events[0]['type'] == 'action'
    TotLogStream.unsubscribe(model_id)
    TotLogStream.unsubscribe(action_id)


def test_multiple_subscribers_and_unsubscribe(initialized_log):
    """多个订阅者均可收到事件，退订后不再回调。"""
    first, second = [], []
    first_id = TotLogStream.subscribe(first.append)
    second_id = TotLogStream.subscribe(second.append)

    TotLogStream.add_model_log(1, 'x', 'before')
    assert len(first) == len(second) == 1
    assert TotLogStream.unsubscribe(first_id)
    assert not TotLogStream.unsubscribe(999999)
    TotLogStream.add_model_log(2, 'x', 'after')

    assert len(first) == 1
    assert len(second) == 2
    assert TotLogStream.unsubscribe(second_id)


def test_handler_exception_does_not_break_logging(initialized_log):
    """订阅回调异常不应阻断后续派发或文件写入。"""
    received = []

    def failing_handler(_event):
        raise RuntimeError('expected test failure')

    bad_id = TotLogStream.subscribe(failing_handler)
    good_id = TotLogStream.subscribe(received.append)
    TotLogStream.add_model_log(1, 'thought', 'payload')
    TotLogStream.write_log()

    assert len(received) == 1
    lines = (initialized_log / 'model.txt').read_text().splitlines()
    assert json.loads(lines[0])['item'] == 'payload'
    TotLogStream.unsubscribe(bad_id)
    TotLogStream.unsubscribe(good_id)


def test_concurrent_add_dispatches_all_events(initialized_log):
    """并发追加模型和代理日志时，订阅者应收到全部事件且无异常。"""
    events = []
    events_lock = threading.Lock()

    def collect(event):
        with events_lock:
            events.append(event)

    subscription_id = TotLogStream.subscribe(collect)
    thread_count = 8
    events_per_thread = 50

    def add_events(thread_id):
        for index in range(events_per_thread):
            if thread_id % 2:
                TotLogStream.add_agent_log(index, 'action', thread_id, 0)
            else:
                TotLogStream.add_model_log(index, 'thought', thread_id)

    threads = [threading.Thread(target=add_events, args=(thread_id,)) for thread_id in range(thread_count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(events) == thread_count * events_per_thread
    TotLogStream.unsubscribe(subscription_id)


def test_subscribe_requires_callable(initialized_log):
    """非可调用对象不能注册为订阅处理器。"""
    with pytest.raises(TypeError):
        TotLogStream.subscribe('not-callable')


def test_init_log_clear_old_removes_previous_files(tmp_path):
    """clear_old=True 时应删除旧日志，后续写入只保留新内容。"""
    (tmp_path / 'model.txt').write_text('old-model\n')
    (tmp_path / 'agent_0.txt').write_text('old-agent\n')
    (tmp_path / 'agent_9.txt').write_text('old-agent-9\n')
    (tmp_path / 'event.txt').write_text('old-event\n')

    TotLogStream.init_log(1, str(tmp_path), clear_old=True, buffer_size=100)
    TotLogStream.add_model_log(1, 'new', 'new-model')
    TotLogStream.write_log()

    assert (tmp_path / 'model.txt').read_text() != 'old-model\n'
    assert 'old-model' not in (tmp_path / 'model.txt').read_text()
    assert not (tmp_path / 'agent_0.txt').exists()
    assert not (tmp_path / 'agent_9.txt').exists()
    assert not (tmp_path / 'event.txt').exists()


def test_init_log_default_preserves_previous_files(tmp_path):
    """clear_old=False（默认）时应保留旧内容并追加新日志。"""
    (tmp_path / 'model.txt').write_text('old-model\n')

    TotLogStream.init_log(1, str(tmp_path), buffer_size=100)
    TotLogStream.add_model_log(1, 'new', 'new-model')
    TotLogStream.write_log()

    content = (tmp_path / 'model.txt').read_text()
    assert 'old-model\n' in content
    assert json.loads(content.splitlines()[-1])['item'] == 'new-model'


def test_add_without_subscribers_is_valid(initialized_log):
    """没有订阅者时追加日志应正常完成。"""
    TotLogStream.add_model_log(1, 'thought', 'payload')
    assert TotLogStream.model_log[-1]['item'] == 'payload'
