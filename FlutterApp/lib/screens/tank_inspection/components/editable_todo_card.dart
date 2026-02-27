

/*
class EditableTodoCard extends StatefulWidget {
  final CheckListRequest todo;
  final Function(CheckListRequest updated) onSave;

  const EditableTodoCard({
    super.key,
    required this.todo,
    required this.onSave,
  });

  @override
  State<EditableTodoCard> createState() => _EditableTodoCardState();
}

class _EditableTodoCardState extends State<EditableTodoCard> {
  late String status;
  late List<Section> items;
  late List<TextEditingController> controllers;


  @override
  void initState() {
    super.initState();

    status = widget.todo.status;

    items = widget.todo.items
        .map((e) => Section(
      sn: e.sn,
      title: e.title,
      comments: e.comment,
    ))
        .toList();

    print("APPLY TODO CHANGES:");
    for (var t in items) {
      print("ITEM ${t.sn}: ${t.comment}");

    }

    controllers = items
        .map((item) => TextEditingController(text: item.comment ?? ""))
        .toList();
  }

  @override
  void dispose() {
    for (var c in controllers) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  void didUpdateWidget(covariant EditableTodoCard oldWidget) {
    super.didUpdateWidget(oldWidget);

    if (oldWidget.todo != widget.todo) {
      // Update status
      status = widget.todo.status;

      // Update items
      items = widget.todo.items
          .map((e) => Section(
        sn: e.sn,
        title: e.title,
        comment: e.comment,
      ))
          .toList();

      // Update controllers
      controllers.forEach((c) => c.dispose());
      controllers = items
          .map((item) => TextEditingController(text: item.comment ?? ""))
          .toList();

      setState(() {});
    }
  }


  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 3,
      margin: const EdgeInsets.only(bottom: 16),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [

            // TITLE (section)
            Text(widget.todo.title,
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),

            const SizedBox(height: 12),

            // -----------------------------------
            // SUB ITEMS
            // -----------------------------------
            ...items.asMap().entries.map((entry) {
              int index = entry.key;
              var item = entry.value;
              var controller = controllers[index];

              return Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text("${item.sn}  ${item.title}", style: const TextStyle(fontSize: 15)),
                    const SizedBox(height: 6),

                    TextField(
                      controller: controller,
                      maxLines: 3,
                      onChanged: (v) => item.comment = v,
                      decoration: InputDecoration(
                        hintText: "Enter comment...",
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                    ),
                  ],
                ),
              );
            }),

            const Divider(height: 24),

            // -----------------------------------
            // LEGEND
            // -----------------------------------
            const Text("Legend for Status:",
                style: TextStyle(fontWeight: FontWeight.bold)),

            Row(
              children: [
                radio("ok", "✓ OK"),
                radio("faulty", "X Faulty"),
                radio("na", "NA"),
              ],
            ),

            const SizedBox(height: 20),

            // SAVE BUTTON
            Align(
              alignment: Alignment.centerRight,
              child: ElevatedButton(
                onPressed: () {
                  widget.onSave(
                    TodoItem(
                      title: widget.todo.title,
                      isChecked: widget.todo.isChecked,
                      status: status,
                      items: items,
                    ),
                  );
                },
                child: const Text("Save Changes"),
              ),
            )
          ],
        ),
      ),
    );
  }

  Widget radio(String value, String label) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Radio(
          value: value,
          groupValue: status,
          onChanged: (v) {
            setState(() => status = v!);
          },
        ),
        Text(label),
        const SizedBox(width: 12),
      ],
    );
  }
}
*/
