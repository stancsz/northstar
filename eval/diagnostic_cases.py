"""Project-authored diagnostic fixtures, with verifiers kept outside agent containers."""

from __future__ import annotations

from textwrap import dedent


# Each tuple contains a task, initial implementation, public assertion, and held-out assertions.
CASES = (
    (
        "expiry-boundary", "Make get(key, now) return the value only while now is strictly before expiry. "
        "A None expiry never expires. get must never remove entries.",
        """
        entries = {'zero': ('z', 0), 'open': ('o', None), 'soon': ('s', 10)}
        def operation(key, now):
            row = entries.get(key)
            if row and (not row[1] or row[1] >= now):
                return row[0]
        """,
        "assert get('soon', 10) is None",
        """
        assert get('zero', 0) is None
        assert get('zero', -1) == 'z'
        assert get('open', 10**6) == 'o'
        assert get('soon', 9) == 's'
        assert get('missing', 0) is None
        assert get('soon', 11) is None and get('soon', 9) == 's'
        """,
    ),
    (
        "route-segment-boundary", "Make route(path, rules) return the value for the longest matching segment prefix. "
        "The root prefix matches all paths. Exact prefixes and their slash-delimited descendants match.",
        """
        def operation(path, rules):
            for key, value in rules.items():
                if path.startswith(key):
                    return value
        """,
        "assert route('/reports/weekly', {'/': 0, '/reports': 1}) == 1",
        """
        rules = {'/': 0, '/cat': 1, '/catalog': 2, '/catalog/items': 3}
        assert route('/catalog/items', rules) == 3
        assert route('/catalog/items/6', rules) == 3
        assert route('/caterpillar', rules) == 0
        assert route('/cat', rules) == 1
        assert route('/missing', {'/cat': 1}) is None
        """,
    ),
    (
        "overlapping-ranges", "Make merge(ranges) return sorted, coalesced half-open ranges. Merge touching, "
        "overlapping, and nested ranges. Drop empty ranges and preserve the original input.",
        """
        def operation(ranges):
            out = []
            for start, end in sorted(ranges):
                if out and start < out[-1][1]:
                    out[-1] = (out[-1][0], end)
                else:
                    out.append((start, end))
            return out
        """,
        "assert merge([(1, 3), (3, 5)]) == [(1, 5)]",
        """
        rows = [(4, 5), (7, 9), (0, 6), (6, 7), (15, 15), (-5, -1)]
        assert merge(rows) == [(-5, -1), (0, 9)]
        assert rows == [(4, 5), (7, 9), (0, 6), (6, 7), (15, 15), (-5, -1)]
        assert merge([]) == []
        """,
    ),
    (
        "nested-config-copy", "Make resolve(base, override) recursively merge dictionaries. Override scalar and list values "
        "replace base values, including None. Return a deep copy with no aliases to either input.",
        """
        def operation(base, override):
            result = dict(base)
            result.update({key: value for key, value in override.items() if value is not None})
            return result
        """,
        "assert resolve({'a': {'x': 1}}, {'a': {'y': 2}}) == {'a': {'x': 1, 'y': 2}}",
        """
        a = {'opts': {'a': [1], 'b': 2}, 'clear': 1, 'items': [1, 2]}
        b = {'opts': {'c': {'d': 3}}, 'clear': None, 'items': []}
        result = resolve(a, b)
        assert result == {'opts': {'a': [1], 'b': 2, 'c': {'d': 3}}, 'clear': None, 'items': []}
        result['opts']['a'].append(4)
        result['opts']['c']['d'] = 5
        assert a['opts']['a'] == [1] and b['opts']['c']['d'] == 3
        assert resolve({'k': {'a': 1}}, {'k': 0}) == {'k': 0}
        """,
    ),
    (
        "stable-batched-pagination", "Make page(rows, cursor, limit) sort by (time, id) and return the rows strictly "
        "after cursor, at most limit rows. Return a next cursor only when more rows remain. None starts from the beginning.",
        """
        def operation(rows, cursor, limit):
            result = sorted(rows, key=lambda row: row[0])
            if cursor:
                result = [row for row in result if row[0] >= cursor[0]]
            result = result[:limit]
            return result, result[-1] if len(result) == limit else None
        """,
        "assert page([(1,'a'), (1,'b'), (2,'a')], (1,'a'), 1) == ([(1,'b')], (1,'b'))",
        """
        rows = [(2,'c'), (0,'b'), (0,'a'), (9,'d')]
        assert page(rows, None, 2) == ([(0,'a'), (0,'b')], (0,'b'))
        assert page(rows, (0,'b'), 2) == ([(2,'c'), (9,'d')], None)
        assert page(rows, (10,'x'), 1) == ([], None)
        assert page(rows, None, 8) == (sorted(rows), None)
        """,
    ),
    (
        "event-replay-tombstone", "Make latest(events) return active id-to-value entries. The highest sequence "
        "number per id wins regardless of delivery order. A winning None is a tombstone. Later list position breaks sequence ties.",
        """
        def operation(events):
            return {key: value for key, seq, value in events if value is not None}
        """,
        "assert latest([('x', 5, None), ('x', 4, 'old')]) == {}",
        """
        rows = [('x', 4, 'ok'), ('a', 1, 'a'), ('x', 6, None), ('x', 2, 'old'), ('a', 1, 'b')]
        assert latest(rows) == {'a': 'b'}
        assert latest([('z', 6, None), ('z', 7, 0)]) == {'z': 0}
        assert latest([('z', 1, 'x'), ('z', 1, None)]) == {}
        """,
    ),
    (
        "lru-read-touch", "Make cache(operations, capacity) return get results in order. A successful get and every put "
        "make the key most recently used. Inserting above capacity evicts the least recently used key. Zero capacity stores nothing.",
        """
        def operation(operations, capacity):
            values = {}
            results = []
            for action, key, *data in operations:
                if action == 'get':
                    results.append(values.get(key))
                else:
                    values[key] = data[0]
                    if len(values) > capacity:
                        values.pop(next(iter(values)))
            return results
        """,
        "assert cache([('put','a',1),('put','b',2),('get','a'),('put','c',3),('get','b')],2) == [1,None]",
        """
        ops = [('put','a',1),('put','b',2),('put','a',4),('get','missing'),('put','c',3),('get','b'),('get','a')]
        assert cache(ops, 2) == [None, None, 4]
        assert cache([('put','a',0),('get','a')], 0) == [None]
        assert cache([('put','a',None),('put','b',2),('get','a'),('put','c',3),('get','b')], 2) == [None, None]
        """,
    ),
    (
        "normalised-clock", "Make minute(timestamp) return the UTC minute of day for an ISO-8601 timestamp with an offset. "
        "Conversion can cross midnight. A naive timestamp raises ValueError.",
        """
        from datetime import datetime
        def operation(timestamp):
            result = datetime.fromisoformat(timestamp)
            return result.hour * 60 + result.minute
        """,
        "assert minute('2026-01-02T00:15:00+01:00') == 1395",
        """
        assert minute('2026-07-12T23:55:30-01:00') == 55
        assert minute('2026-07-12T06:11:00+05:30') == 41
        assert minute('2026-01-01T11:03:00Z') == 663
        try:
            minute('2026-01-01T11:03:00')
        except ValueError:
            pass
        else:
            raise AssertionError('naive input was accepted')
        """,
    ),
    (
        "patch-removal-order", "Make update(values, operations) apply operations in order. A None value deletes the "
        "key, including a missing key. Later writes may restore it. The original dictionary must stay unchanged.",
        """
        def operation(values, operations):
            values.update({key: value for key, value in operations if value is not None})
            return values
        """,
        "assert update({'x': 1}, [('x', None)]) == {}",
        """
        original = {'x': 1, 'y': 2}
        assert update(original, [('x', None), ('z', None), ('x', 0), ('y', None)]) == {'x': 0}
        assert original == {'x': 1, 'y': 2}
        assert update({}, [('x', False), ('x', None), ('z', '')]) == {'z': ''}
        """,
    ),
    (
        "ordered-dependency-walk", "Make plan(graph, target) return prerequisites before dependants and include target. "
        "Maintain each prerequisite list's order, deduplicate shared prerequisites, and raise ValueError on reachable cycles.",
        """
        def operation(graph, target):
            output = []
            def visit(node):
                for dependency in graph.get(node, []):
                    visit(dependency)
                output.append(node)
            visit(target)
            return output
        """,
        "assert plan({'t':['a','b'], 'a':['c'], 'b':['c']},'t') == ['c','a','b','t']",
        """
        assert plan({'a':['d','c','c'], 'c':['d'], 'unreachable':['unreachable']}, 'a') == ['d','c','a']
        assert plan({},'single') == ['single']
        try:
            plan({'a':['b'], 'b':['c'], 'c':['a']},'a')
        except ValueError:
            pass
        else:
            raise AssertionError('cycle was accepted')
        """,
    ),
    (
        "snapshot-filter", "Make sample(rows, labels) return independent copies of rows whose tags contain every "
        "requested label. Input rows have list-valued tags and optional nested attributes. Preserve order.",
        """
        def operation(rows, labels):
            return [row for row in rows if set(row['tags']).intersection(labels)]
        """,
        "assert sample([{'tags':['a']}], ['a','b']) == []",
        """
        rows = [{'tags':['a','b'], 'attrs':{'levels':[1]}}, {'tags':['b']}, {'tags':[]}]
        result = sample(rows, ['b','a','b'])
        assert result == rows[:1]
        result[0]['attrs']['levels'].append(7)
        assert rows[0]['attrs']['levels'] == [1]
        assert sample(rows, []) == rows
        """,
    ),
    (
        "window-count-strict-edge", "Make windows(points, span) return one count per point in its original order. "
        "Count points with time in (point - span, point], including every duplicate at the current time.",
        """
        def operation(points, span):
            ordered = sorted(points)
            return [sum(point - span <= previous <= point for previous in ordered) for point in ordered]
        """,
        "assert windows([3, 1, 2], 2) == [2, 1, 2]",
        """
        assert windows([7, 7, 4, 10], 3) == [2, 2, 1, 1]
        assert windows([-4, 1, -2], 4) == [1, 2, 2]
        assert windows([0, 0], 1) == [2, 2]
        assert windows([], 4) == []
        """,
    ),
    (
        "weighted-aggregator", "Make average(records) compute the weighted mean of numeric values and integer weights. "
        "Ignore missing values (None), keep numeric zeros, and return None when contributing weight is zero.",
        """
        def operation(records):
            included = [v for v, weight in records if v]
            return sum(included) / len(included) if included else 0
        """,
        "assert average([(0, 3), (8, 1)]) == 2",
        """
        assert average([(None, 100), (0, 2), (15, 3)]) == 9
        assert average([(1, 0), (None, 500)]) is None
        assert average([(-2, 3), (4, 2)]) == 0.4
        assert average([]) is None
        """,
    ),
    (
        "replay-ack-watermark", "Make watermark(acked, start) return the largest contiguous acknowledged number from "
        "start onward, or start-1 if start is unacknowledged. Ack input can be unordered and contain duplicates.",
        """
        def operation(acked, start):
            return max(acked, default=start - 1)
        """,
        "assert watermark([5, 1, 2], 1) == 2",
        """
        assert watermark([4, 3, 3, 20, 5], 3) == 5
        assert watermark([0, 1, 4], 3) == 2
        assert watermark([-4, -3, -2], -4) == -2
        assert watermark([], 3) == 2
        """,
    ),
    (
        "selector-stable-tie", "Make choose(candidates, threshold) return the highest-score candidate's id among "
        "eligible candidates. Eligibility means active and score >= threshold. Earlier list order wins ties.",
        """
        def operation(candidates, threshold):
            matches = [(score, key) for key, score, active in candidates if score > threshold]
            return max(matches)[1] if matches else None
        """,
        "assert choose([('inactive', 10, False), ('valid', 4, True)], 4) == 'valid'",
        """
        assert choose([('a', 9, True), ('z', 9, True), ('m', 7, True)], 7) == 'a'
        assert choose([('x', 9, False), ('y', 1, True)], 2) is None
        assert choose([('z', 0, True)], 0) == 'z'
        assert choose([], 0) is None
        """,
    ),
    (
        "prediction-field-escaping", "Make serialize(records) return one TSV line per (id, payload), joined by newline "
        "without a trailing newline. Escape backslashes, tabs, carriage returns, and newlines in both fields.",
        """
        def operation(records):
            return '\\n'.join(key + '\\t' + val.replace('\\n', '\\\\n') for key, val in records)
        """,
        r"assert serialize([('a' + chr(9), chr(92))]) == 'a\\t' + chr(9) + '\\\\'",
        r"""
        assert serialize([('x', 'literal\\n\n\r\t')]) == 'x\tliteral\\\\n\\n\\r\\t'
        assert serialize([('a','b'), ('c\r','d')]) == 'a\tb\nc\\r\td'
        assert serialize([]) == ''
        """,
    ),
)


def diagnostic_tasks(task_class):
    tasks = []
    for name, goal, implementation, public_check, held_out in CASES:
        function = goal.split("(", 1)[0].split()[-1]
        boundary = f"from core import operation as {function}\n"
        check = f"from api import {function}\n"
        tasks.append(task_class(
            id="diagnostic-" + name, suite="diagnostic", goal=goal,
            constraints=("Preserve the exported function name and signature.", "Use Python's standard library."),
            acceptance="The public assertion and independent checks for the stated edge cases pass.",
            inputs={"core.py": dedent(implementation).lstrip(), "api.py": boundary, "check.py": check + public_check + "\n"},
            grader=check + dedent(held_out).lstrip(),
        ))
    return tasks
