#!/usr/bin/env python3
import frontmatter
import inspect

print(help(frontmatter))

print("Available functions and methods in frontmatter:")
print("=" * 50)

# # Get all attributes
# for name in dir(frontmatter):
#     # Skip private or dunder methods
#     if name.startswith('_'):
#         continue

#     attr = getattr(frontmatter, name)

#     # Check if it's a function, method or class
#     if inspect.isfunction(attr) or inspect.isclass(attr) or inspect.ismethod(attr):
#         print(f"{name}: {type(attr).__name__}")

#         # For functions and methods, print signature
#         if inspect.isfunction(attr) or inspect.ismethod(attr):
#             try:
#                 sig = inspect.signature(attr)
#                 print(f"  Signature: {name}{sig}")
#             except (ValueError, TypeError):
#                 print(f"  Signature: Could not determine")

#         # For classes, print methods
#         if inspect.isclass(attr):
#             print("  Methods:")
#             for class_name in dir(attr):
#                 if not class_name.startswith('_'):
#                     class_attr = getattr(attr, class_name)
#                     if inspect.isfunction(class_attr) or inspect.ismethod(class_attr):
#                         try:
#                             class_sig = inspect.signature(class_attr)
#                             print(f"    {class_name}{class_sig}")
#                         except (ValueError, TypeError):
#                             print(f"    {class_name}: Could not determine signature")

#         print()

# # Try to use some common functions
# print("\nExample usages:")
# print("=" * 50)

# try:
#     print("Checking if parse function exists:")
#     if hasattr(frontmatter, 'parse'):
#         print("  parse function exists")
#         print("  Signature:", inspect.signature(frontmatter.parse))
# except Exception as e:
#     print(f"  Error checking parse: {e}")

# try:
#     print("\nChecking if load function exists:")
#     if hasattr(frontmatter, 'load'):
#         print("  load function exists")
#         print("  Signature:", inspect.signature(frontmatter.load))
# except Exception as e:
#     print(f"  Error checking load: {e}")

# try:
#     print("\nChecking if dumps function exists:")
#     if hasattr(frontmatter, 'dumps'):
#         print("  dumps function exists")
#         print("  Signature:", inspect.signature(frontmatter.dumps))
# except Exception as e:
#     print(f"  Error checking dumps: {e}")
