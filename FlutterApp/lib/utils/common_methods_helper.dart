

import 'package:flutter/material.dart';

Future<void> showPermissionDialog({
  required BuildContext context,
  required String title,
  required String message,
  required VoidCallback onSettingsPressed,
}) async {
  return showDialog(
    context: context,
    barrierDismissible: false,
    builder: (context) {
      return AlertDialog(
        title: Text(title),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context), // dismiss
            child: const Text("Cancel"),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              onSettingsPressed();
            },
            child: const Text("Open Settings"),
          ),
        ],
      );
    },
  );
}
