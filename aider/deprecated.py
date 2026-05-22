def add_deprecated_model_args(parser, group):
    """Add deprecated model shortcut arguments to the argparse parser."""
    gpt_4_model = "openai/gpt-4-0613"
    group.add_argument(
        "--4",
        "-4",
        action="store_true",
        help=f"Use {gpt_4_model} model for the main chat (deprecated, use --model)",
        default=False,
    )
    gpt_4o_model = "openai/gpt-4o"
    group.add_argument(
        "--4o",
        action="store_true",
        help=f"Use {gpt_4o_model} model for the main chat (deprecated, use --model)",
        default=False,
    )
    gpt_4o_mini_model = "openai/gpt-4o-mini"
    group.add_argument(
        "--mini",
        action="store_true",
        help=f"Use {gpt_4o_mini_model} model for the main chat (deprecated, use --model)",
        default=False,
    )
    gpt_4_turbo_model = "openai/gpt-4-1106-preview"
    group.add_argument(
        "--4-turbo",
        action="store_true",
        help=f"Use {gpt_4_turbo_model} model for the main chat (deprecated, use --model)",
        default=False,
    )
    gpt_3_model_name = "openai/gpt-3.5-turbo"
    group.add_argument(
        "--35turbo",
        "--35-turbo",
        "--3",
        "-3",
        action="store_true",
        help=f"Use {gpt_3_model_name} model for the main chat (deprecated, use --model)",
        default=False,
    )
    o1_mini_model = "openai/o1-mini"
    group.add_argument(
        "--o1-mini",
        action="store_true",
        help=f"Use {o1_mini_model} model for the main chat (deprecated, use --model)",
        default=False,
    )
    o1_preview_model = "openai/o1-preview"
    group.add_argument(
        "--o1-preview",
        action="store_true",
        help=f"Use {o1_preview_model} model for the main chat (deprecated, use --model)",
        default=False,
    )


def handle_deprecated_model_args(args, io):
    """Handle deprecated model shortcut arguments and provide appropriate warnings."""
    # Define model mapping
    model_map = {
        "4": "openai/gpt-4-0613",
        "4o": "openai/gpt-4o",
        "mini": "openai/gpt-4o-mini",
        "4_turbo": "openai/gpt-4-1106-preview",
        "35turbo": "openai/gpt-3.5-turbo",
        "o1_mini": "openai/o1-mini",
        "o1_preview": "openai/o1-preview",
    }

    # Check if any deprecated args are used
    for arg_name, model_name in model_map.items():
        arg_name_clean = arg_name.replace("-", "_")
        if hasattr(args, arg_name_clean) and getattr(args, arg_name_clean):
            # Find preferred name to display in warning
            from aider.models import MODEL_ALIASES

            display_name = model_name
            # Check if there's a shorter alias for this model
            for alias, full_name in MODEL_ALIASES.items():
                if full_name == model_name:
                    display_name = alias
                    break

            # Show the warning
            io.tool_warning(
                f"The --{arg_name.replace('_', '-')} flag is deprecated and will be removed in a"
                f" future version. Please use --model {display_name} instead."
            )

            # Set the model
            if not args.model:
                args.model = model_name
            break
