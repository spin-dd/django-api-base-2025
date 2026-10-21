# queryset の JOIN 判定

`apibase.querysets.duplicating_join_aliases(queryset)` は、元の行を複製しうる
JOIN の alias を `set[str]` で返します。逆 FK、M2M、GenericRelation を含み、
単値 FK と一対一の JOIN は含みません。SQL は実行しません。

```python
from apibase.querysets import duplicating_join_aliases

base_aliases = duplicating_join_aliases(base_queryset)
filtered_aliases = duplicating_join_aliases(filtered_queryset)
new_fan_out = filtered_aliases - base_aliases
```

REST 側は `new_fan_out` から新たに張られた多値 JOIN を検査できます。
GraphQL 側も同じ判定を使い、判定中に例外が起きた場合は従来どおり
保守的に `DISTINCT` を適用します。alias の集合は行数を保証するものではなく、
JOIN が行を複製しうるかを示します。
