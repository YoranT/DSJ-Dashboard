"""Register the frontend in Lovelace as well as the global module loader."""

async def ensure_lovelace_resource(resources, module_url):
    """Use the public collection API; preserve unrelated resources."""
    await resources.async_get_info()
    base_url = module_url.split("?", 1)[0]
    matches = [item for item in resources.async_items() if item.get("url", "").split("?", 1)[0] == base_url]
    if hasattr(resources, "async_create_item"):
        if not matches:
            await resources.async_create_item({"res_type": "module", "url": module_url})
        else:
            for item in matches:
                if item["url"] != module_url or item.get("type") != "module":
                    await resources.async_update_item(item["id"], {"res_type": "module", "url": module_url})
    elif not matches:
        # YAML resource collections are in-memory snapshots of the user's YAML.
        # Add only our runtime resource; never edit configuration.yaml.
        resources.data.append({"id": "dsj_dashboard", "type": "module", "url": module_url})
    else:
        for item in matches:
            item.update(type="module", url=module_url)
