"""PubTabNet Tree-Edit-Distance-based Similarity (TEDS).

Adapted from PubTabNet ``src/metric.py`` for sequential evaluation only.
Copyright 2020 IBM, Apache License 2.0.
"""

from __future__ import annotations

from collections import deque

import distance
from apted import APTED, Config
from apted.helpers import Tree
from lxml import etree, html


class TableTree(Tree):
    def __init__(self, tag, colspan=None, rowspan=None, content=None, *children):
        self.tag = tag
        self.colspan = colspan
        self.rowspan = rowspan
        self.content = content
        self.children = list(children)


class CustomConfig(Config):
    @staticmethod
    def normalized_distance(left, right) -> float:
        maximum = max(len(left), len(right))
        return float(distance.levenshtein(left, right)) / maximum if maximum else 0.0

    def rename(self, node1, node2):
        if (node1.tag, node1.colspan, node1.rowspan) != (node2.tag, node2.colspan, node2.rowspan):
            return 1.0
        if node1.tag == "td" and (node1.content or node2.content):
            return self.normalized_distance(node1.content, node2.content)
        return 0.0


class TEDS:
    def __init__(self, structure_only: bool = False, ignore_nodes=None):
        self.structure_only = structure_only
        self.ignore_nodes = ignore_nodes
        self._tokens: list[str] = []

    def tokenize(self, node) -> None:
        self._tokens.append(f"<{node.tag}>")
        if node.text is not None:
            self._tokens += list(node.text)
        for child in node.getchildren():
            self.tokenize(child)
        if node.tag != "unk":
            self._tokens.append(f"</{node.tag}>")
        if node.tag != "td" and node.tail is not None:
            self._tokens += list(node.tail)

    def load_html_tree(self, node, parent=None):
        if node.tag == "td":
            if self.structure_only:
                cell = []
            else:
                self._tokens = []
                self.tokenize(node)
                cell = self._tokens[1:-1].copy()
            new_node = TableTree(
                node.tag,
                int(node.attrib.get("colspan", "1")),
                int(node.attrib.get("rowspan", "1")),
                cell,
                *deque(),
            )
        else:
            new_node = TableTree(node.tag, None, None, None, *deque())
        if parent is not None:
            parent.children.append(new_node)
        if node.tag != "td":
            for child in node.getchildren():
                self.load_html_tree(child, new_node)
        return new_node if parent is None else None

    def evaluate(self, pred: str, true: str) -> float:
        if not pred or not true:
            return 0.0
        parser = html.HTMLParser(remove_comments=True, encoding="utf-8")
        pred_tree = html.fromstring(pred, parser=parser)
        true_tree = html.fromstring(true, parser=parser)
        pred_tables = pred_tree.xpath("body/table")
        true_tables = true_tree.xpath("body/table")
        if not pred_tables or not true_tables:
            return 0.0
        pred_table, true_table = pred_tables[0], true_tables[0]
        if self.ignore_nodes:
            etree.strip_tags(pred_table, *self.ignore_nodes)
            etree.strip_tags(true_table, *self.ignore_nodes)
        node_count = max(len(pred_table.xpath(".//*")), len(true_table.xpath(".//*")))
        if node_count == 0:
            return 0.0
        edit_distance = APTED(
            self.load_html_tree(pred_table), self.load_html_tree(true_table), CustomConfig()
        ).compute_edit_distance()
        return 1.0 - float(edit_distance) / node_count


def self_check() -> None:
    sample = "<html><body><table><tbody><tr><td>A</td></tr></tbody></table></body></html>"
    assert TEDS().evaluate(sample, sample) == 1.0
    assert TEDS(structure_only=True).evaluate(sample, sample) == 1.0


if __name__ == "__main__":
    self_check()
    print("self-check: OK")
