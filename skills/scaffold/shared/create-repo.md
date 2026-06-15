# Shared: Clone Template + Strip History + Push

> Called from step-1b files after the remote repo is created.
> Caller must set: `$TEMPLATE_URL`, `$REMOTE_URL`, `$LOCAL_DIR`

```bash
git clone --depth 1 "$TEMPLATE_URL" "$LOCAL_DIR"
rm -rf "$LOCAL_DIR/.git"
git -C "$LOCAL_DIR" init -b main
git -C "$LOCAL_DIR" remote add origin "$REMOTE_URL"
git -C "$LOCAL_DIR" add -A
git -C "$LOCAL_DIR" commit -m "chore: initial scaffold from coco-agent template [skip ci]"
git -C "$LOCAL_DIR" push -u origin main
```

Result: single clean commit — no template git history in the user's repo.
