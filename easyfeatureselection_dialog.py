from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QListWidget, QLineEdit, QCheckBox, QPushButton, QSlider, QWidget, QTableWidget, QTableWidgetItem, QRadioButton, QButtonGroup, QComboBox as QCombo, QStyle, QSizePolicy, QSplitter
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QClipboard
from qgis.core import QgsProject, QgsMapLayer, QgsRasterLayer, QgsCoordinateTransform, QgsCoordinateReferenceSystem, QgsFeatureRequest, QgsMapLayerProxyModel, Qgis
from qgis.gui import QgsCollapsibleGroupBox, QgsMessageBar, QgsMapLayerComboBox
from qgis.utils import iface
from PyQt5.QtWidgets import QApplication, QHeaderView, QAbstractItemView
from PyQt5.QtCore import QTimer, QPoint, pyqtSignal  

class EasyFeatureSelectionDialog(QDialog):
    _instance = None  # Singleton instance for dialog
    closingPlugin = pyqtSignal()  # Define the closingPlugin signal

    @classmethod
    def show_dialog(cls):
        # Check if there is an open project with layers
        if not QgsProject.instance().mapLayers():
            # Show a notification box if no project is open and return immediately
            iface.messageBar().pushMessage(
                "No Project Open",
                "No project is open. Create a new one or open an existing one to start using these tools.",
                level=Qgis.Warning,  # Corrected to use Qgis.Warning
                duration=3
            )
            return  # Return immediately to prevent the dialog from being shown

        if cls._instance is None:
            cls._instance = EasyFeatureSelectionDialog()

        cls._instance.show()
        cls._instance.raise_()  # Bring the dialog to the front

    def __init__(self):
        super().__init__(iface.mainWindow())
        self.setWindowTitle('Easy Feature Selector')
        self.setWindowModality(Qt.NonModal)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(Qt.Window | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)

        # Main Layout
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        # Create a widget to hold the splitter
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.content_widget)
        
        # Create splitter
        self.splitter = QSplitter(Qt.Horizontal)
        self.content_layout.addWidget(self.splitter)

        # Left Panel Layout (including layer selection and feature attribute groups)
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_layout.setContentsMargins(5, 5, 5, 5)
        self.left_layout.setSpacing(5)  # Space between group boxes
        
        # Set minimum width for left panel
        self.left_panel.setMinimumWidth(400)
        self.splitter.addWidget(self.left_panel)

        # QGIS-style message bar
        self.message_bar = QgsMessageBar()
        self.left_layout.addWidget(self.message_bar)

        # Layer Selection GroupBox
        self.layer_group_box = QgsCollapsibleGroupBox("Layer Selection")
        self.layer_group_box.setStyleSheet("""
            QgsCollapsibleGroupBox {
                border: 1px solid #b9b9b9;
                margin-top: 15px;  /* Add space for title */
                padding-top: 8px;  /* Space between title and content */
            }
            QgsCollapsibleGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 3px;
                left: 5px;
                top: -10px;  /* Pull the title up */
            }
        """)
        self.layer_group_box.setChecked(True)
        self.layer_group_layout = QVBoxLayout()
        self.layer_group_layout.setSpacing(3)  # Reduce spacing between widgets
        
        # Layer selection widgets
        self.layer_combo_box = QgsMapLayerComboBox()
        self.layer_combo_box.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.layer_combo_box.currentIndexChanged.connect(self.on_layer_changed_from_combo)
        self.layer_group_layout.addWidget(self.layer_combo_box)
        
        # Add raster warning label
        self.raster_warning = QLabel("This Plugin Supports Only Vectors")
        self.raster_warning.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        self.raster_warning.hide()
        self.layer_group_layout.addWidget(self.raster_warning)
        
        self.layer_label = QLabel("Select Field from List:")
        self.layer_group_layout.addWidget(self.layer_label)
        
        self.dynamic_layer_switch = QCheckBox()
        self.dynamic_layer_switch.setText("Allow dynamic Layer Selection")
        self.dynamic_layer_switch.setChecked(False)
        self.dynamic_layer_switch.stateChanged.connect(self.toggle_dynamic_layer_selection)
        self.layer_group_layout.addWidget(self.dynamic_layer_switch)

        self.layer_group_box.setLayout(self.layer_group_layout)
        self.left_layout.addWidget(self.layer_group_box)

        # Field Selection GroupBox
        self.field_group_box = QgsCollapsibleGroupBox("Field Selection")
        self.field_group_box.setStyleSheet("""
            QgsCollapsibleGroupBox {
                border: 1px solid #b9b9b9;
                margin-top: 15px;  /* Add space for title */
                padding-top: 8px;  /* Space between title and content */
            }
            QgsCollapsibleGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 3px;
                left: 5px;
                top: -10px;  /* Pull the title up */
            }
        """)
        self.field_group_box.setChecked(True)
        self.field_group_layout = QVBoxLayout()
        self.field_group_layout.setSpacing(3)  # Reduce spacing between widgets
        
        self.field_label = QLabel("Select Field from Attribute Table:")
        self.field_group_layout.addWidget(self.field_label)
        
        self.field_combo_box = QComboBox()
        self.field_combo_box.currentIndexChanged.connect(self.on_field_changed)
        self.field_group_layout.addWidget(self.field_combo_box)
        
        self.field_group_box.setLayout(self.field_group_layout)
        self.left_layout.addWidget(self.field_group_box)

        # Unique Values GroupBox
        self.values_group_box = QgsCollapsibleGroupBox("Unique Values")
        self.values_group_box.setStyleSheet("""
            QgsCollapsibleGroupBox {
                border: 1px solid #b9b9b9;
                margin-top: 15px;  /* Add space for title */
                padding-top: 8px;  /* Space between title and content */
            }
            QgsCollapsibleGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 3px;
                left: 5px;
                top: -10px;  /* Pull the title up */
            }
        """)
        self.values_group_box.setChecked(True)
        self.values_group_layout = QVBoxLayout()
        self.values_group_layout.setSpacing(3)  # Reduce spacing between widgets
        
        self.unique_values_label = QLabel("Select From the Unique Values")
        self.values_group_layout.addWidget(self.unique_values_label)
        
        self.unique_values_list = QListWidget()
        self.unique_values_list.currentRowChanged.connect(self.highlight_features)
        self.values_group_layout.addWidget(self.unique_values_list)
        
        self.values_group_box.setLayout(self.values_group_layout)
        self.left_layout.addWidget(self.values_group_box)

        # Collapsible GroupBox for search and zoom options
        self.search_group_box = QgsCollapsibleGroupBox("Search and Zoom Options")
        self.search_group_box.setStyleSheet("""
            QgsCollapsibleGroupBox {
                border: 1px solid #b9b9b9;
                margin-top: 15px;  /* Add space for title */
                padding-top: 8px;  /* Space between title and content */
            }
            QgsCollapsibleGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 3px;
                left: 5px;
                top: -10px;  /* Pull the title up */
            }
        """)
        self.search_group_box.setChecked(True)
        self.search_group_layout = QVBoxLayout()
        self.search_group_layout.setSpacing(3)  # Reduce spacing between widgets
        
        self.search_label = QLabel("Search in Unique Values:")
        self.search_group_layout.addWidget(self.search_label)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText('Search...')
        self.search_box.textChanged.connect(self.filter_values)
        self.search_group_layout.addWidget(self.search_box)
        
        # Interactive zoom checkbox
        self.interact_checkbox = QCheckBox("Interactive Zooming and Panning to Selected Features")
        self.interact_checkbox.setChecked(False)  # Set to unchecked by default
        self.search_group_layout.addWidget(self.interact_checkbox)
        
        self.zoom_label = QLabel("Select zoom level:")
        self.search_group_layout.addWidget(self.zoom_label)
        
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(0)
        self.zoom_slider.setMaximum(100)
        self.zoom_slider.setValue(20)
        self.zoom_slider.setTickInterval(5)
        self.zoom_slider.setTickPosition(QSlider.TicksBelow)
        self.search_group_layout.addWidget(self.zoom_slider)
        
        # Two-way selection checkbox
        self.two_way_selection_checkbox = QCheckBox("Enable two-way selection")
        self.two_way_selection_checkbox.setChecked(False)  # Set to unchecked by default
        self.two_way_selection_checkbox.stateChanged.connect(self.toggle_two_way_selection)
        self.search_group_layout.addWidget(self.two_way_selection_checkbox)
        
        self.search_group_box.setLayout(self.search_group_layout)
        self.left_layout.addWidget(self.search_group_box)

        # Close Button
        self.close_button = QPushButton('Close')
        self.close_button.setFixedSize(100, 30)
        self.close_button.clicked.connect(self.close)
        self.left_layout.addWidget(self.close_button)

        # Add stretch to push everything to the top
        self.left_layout.addStretch(1)

        # Feature Attributes Group (Right Panel)
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(5, 5, 5, 5)
        self.right_layout.setSpacing(5)
        self.splitter.addWidget(self.right_panel)
        
        # Create vertical splitter for the right panel
        self.vertical_splitter = QSplitter(Qt.Vertical)
        self.right_layout.addWidget(self.vertical_splitter)
        
        # Table with headers
        self.table_group_box = QgsCollapsibleGroupBox("Feature Attributes")
        self.table_group_box.setStyleSheet("""
            QgsCollapsibleGroupBox {
                border: 1px solid #b9b9b9;
                margin-top: 15px;  /* Add space for title */
                padding-top: 8px;  /* Space between title and content */
            }
            QgsCollapsibleGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 3px;
                left: 5px;
                top: -10px;  /* Pull the title up */
            }
        """)
        self.table_group_box.setChecked(True)
        self.table_layout = QVBoxLayout()
        self.table_layout.setContentsMargins(3, 3, 3, 3)

        # Add checkbox for controlling Additional Selection column
        self.second_level_checkbox = QCheckBox("Allow 2nd Level Selection")
        self.second_level_checkbox.setChecked(False)  # Default to unchecked
        self.second_level_checkbox.stateChanged.connect(self.toggle_additional_selection)
        self.table_layout.insertWidget(0, self.second_level_checkbox)

        # Table widget with increased height
        self.table_widget = QTableWidget()
        self.table_widget.setMinimumHeight(570)  # Reduced to 95% of original height
        self.table_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table_widget.setColumnCount(2)  # Start with 2 columns by default
        self.table_widget.setHorizontalHeaderLabels(["Field Name", "Value"])  # Initial headers without Additional Selection
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setSelectionMode(QAbstractItemView.NoSelection)
        
        # Style the header with right borders
        header_style = """
            QHeaderView::section {
                background-color: #f0f0f0;
                border: none;
                border-right: 1px solid #b9b9b9;
                border-bottom: 1px solid #b9b9b9;
                padding: 4px;
            }
            QHeaderView::section:last {
                border-right: 1px solid #b9b9b9;
            }
        """
        self.table_widget.horizontalHeader().setStyleSheet(header_style)
        
        self.table_layout.addWidget(self.table_widget)
        
        self.table_layout.addStretch()
        self.table_group_box.setLayout(self.table_layout)
        
        # Add table group box to vertical splitter
        self.vertical_splitter.addWidget(self.table_group_box)
        
        # Add copy button with fixed size and left alignment
        self.copy_button = QPushButton("Copy to Clipboard")
        self.copy_button.setFixedWidth(120)  # Fixed width to fit text
        self.copy_button.setFixedHeight(30)  # Match close button height
        self.copy_button.clicked.connect(self.copy_table_data_to_clipboard)
        
        # Create a container widget for left alignment
        copy_button_container = QWidget()
        copy_button_layout = QHBoxLayout(copy_button_container)
        copy_button_layout.setContentsMargins(3, 0, 0, 0)  # Small left margin
        copy_button_layout.addWidget(self.copy_button, 0, Qt.AlignLeft)
        copy_button_layout.addStretch()
        
        # Add copy button container to right panel layout
        self.right_layout.addWidget(copy_button_container)
        
        # Add invisible widget to bottom of vertical splitter
        self.bottom_widget = QWidget()
        self.bottom_widget.setMinimumHeight(0)
        self.vertical_splitter.addWidget(self.bottom_widget)
        
        # Set the splitter sizes to show only the table group initially
        self.vertical_splitter.setSizes([1, 0])
        
        # Hide the splitter handle
        handle = self.vertical_splitter.handle(1)
        handle.setStyleSheet("""
            QSplitterHandle {
                background: transparent;
            }
        """)
        
        # Add stretch to main layout to push everything to top
        self.main_layout.addStretch(1)

        # Connect group box collapse signals to handle dialog resizing
        self.layer_group_box.collapsedStateChanged.connect(self.handle_group_collapse)
        self.field_group_box.collapsedStateChanged.connect(self.handle_group_collapse)
        self.values_group_box.collapsedStateChanged.connect(self.handle_group_collapse)
        self.search_group_box.collapsedStateChanged.connect(self.handle_group_collapse)
        self.table_group_box.collapsedStateChanged.connect(self.handle_group_collapse)

        # Initialize layer and connections
        self.layer = None
        self.radio_button_group = QButtonGroup(self)  # Group for radio buttons
        self.previous_combo_row = None  # Track the row of the previous combo box
        self.current_list_value = None
        self.current_list_field = None
        self.connect_signals()

        # Connect to active layer change signal
        iface.layerTreeView().currentLayerChanged.connect(self.on_layer_changed)
        self.on_layer_changed(iface.activeLayer())  # Initialize with the current active layer

        # Set dialog minimum size and make it resizable
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)  # Set initial size
        
        # Make the dialog resizable
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Set initial splitter position (1/3 for left panel, 2/3 for right panel)
        self.splitter.setSizes([300, 600])
        
        # Set initial heights after a short delay to ensure all widgets are properly laid out
        QTimer.singleShot(0, self.set_initial_heights)
        
    def set_initial_heights(self):
        """Set initial heights of panels to match."""
        # Get the bottom position of the Search and Zoom Options group
        search_group_bottom = (self.search_group_box.mapToParent(QPoint(0, self.search_group_box.height())).y() +
                             self.search_group_box.parentWidget().mapToParent(QPoint(0, 0)).y())
        
        # Get the top position of the Feature Attributes group
        table_group_top = (self.table_group_box.mapToParent(QPoint(0, 0)).y() +
                          self.table_group_box.parentWidget().mapToParent(QPoint(0, 0)).y())
        
        # Calculate required height to match bottom positions
        required_height = search_group_bottom - table_group_top
        
        # Set vertical splitter sizes
        total_height = self.vertical_splitter.height()
        bottom_height = max(0, total_height - required_height)
        self.vertical_splitter.setSizes([required_height, bottom_height])

    def handle_group_collapse(self, collapsed):
        """Handle group box collapse/expand to resize dialog"""
        # Update initial heights
        self.set_initial_heights()
        
        # Allow dialog to resize to minimum size
        self.adjustSize()
        
        # Update splitter sizes after resize
        QTimer.singleShot(0, lambda: self.vertical_splitter.setSizes(self.vertical_splitter.sizes()))

    def connect_signals(self):
        """Connects signals to methods after all methods are defined."""
        if self.layer and not isinstance(self.layer, QgsRasterLayer):
            # Connect to selection changes
            self.layer.selectionChanged.connect(self.populate_table_with_selected_feature)
            
            # Connect to field selection changes
            self.field_combo_box.currentIndexChanged.connect(self.on_field_changed)
            
            # Connect to unique values selection only for highlighting
            self.unique_values_list.currentRowChanged.connect(self.highlight_features)
            
            if self.two_way_selection_checkbox.isChecked():
                self.layer.selectionChanged.connect(self.update_listbox_with_selection)
        self.search_box.textChanged.connect(self.filter_values)
        self.interact_checkbox.stateChanged.connect(self.check_interactive_selection)
        self.zoom_slider.valueChanged.connect(self.update_zoom_label)
        self.two_way_selection_checkbox.stateChanged.connect(self.toggle_two_way_selection)

    def disconnect_signals(self):
        """Disconnect signals from the previous layer."""
        if self.layer and not isinstance(self.layer, QgsRasterLayer):
            try:
                self.layer.selection.Changed.disconnect(self.populate_table_with_selected_feature)
            except (TypeError, AttributeError):
                pass  # Ignore if there are no connections to disconnect

    def on_layer_changed(self, layer):
        """Handle the event when the active layer changes."""
        self.disconnect_signals()  # Disconnect signals from the previous layer
        
        # Clear all widgets first
        self.field_combo_box.clear()
        self.unique_values_list.clear()
        self.clear_table()
        
        if layer and isinstance(layer, QgsRasterLayer):
            self.raster_warning.show()
            return
            
        self.layer = layer
        self.raster_warning.hide()
        self.update_layer(layer)
        self.layer_combo_box.setLayer(layer)  # Update combo box to reflect the current active layer
        self.connect_signals()  # Connect signals to the new layer

    def on_layer_changed_from_combo(self, index):
        """Handle layer changes from the combo box."""
        layer = self.layer_combo_box.currentLayer()
        if self.dynamic_layer_switch.isChecked():
            iface.setActiveLayer(layer)
        self.on_layer_changed(layer)

    def update_layer_combo_box(self):
        """Populate the layer selection combo box."""
        self.layer_combo_box.setLayer(iface.activeLayer())

    def update_layer(self, layer):
        """Update the active layer and UI components."""
        self.layer = layer
        
        # Clear all widgets first
        self.field_combo_box.clear()
        self.unique_values_list.clear()
        self.clear_table()
        
        if layer and layer.type() == QgsMapLayer.VectorLayer:
            self.update_field_names()
            self.update_unique_values()
        else:
            return

    def update_field_names(self):
        """Update the field names in the combo box."""
        if self.layer:
            self.field_combo_box.clear()
            self.field_combo_box.addItems([field.name() for field in self.layer.fields()])
            if self.field_combo_box.count() == 0:
                self.clear_table()

    def on_field_changed(self):
        """Handle field selection change event."""
        if not hasattr(self.layer, 'selectedFeatures'):
            return
        self.update_unique_values()
        # Update the table when field changes
        if self.layer and len(self.layer.selectedFeatures()) > 0:
            self.populate_table_with_selected_feature()

    def update_unique_values(self):
        """Update the list of unique values based on the selected field."""
        self.unique_values_list.clear()
        field_name = self.field_combo_box.currentText()
        if self.layer and field_name:
            unique_values = set(str(f[field_name]) for f in self.layer.getFeatures() if f[field_name] is not None)
            self.unique_values_list.addItems(sorted(unique_values))
        else:
            self.clear_table()

    def clear_table(self):
        """Clear the table of feature attributes."""
        self.table_widget.setRowCount(0)

    def populate_table_with_selected_feature(self):
        """Populate the table with attributes of the selected feature."""
        self.table_widget.clearContents()
        if self.layer and len(self.layer.selectedFeatures()) == 1:
            feature = self.layer.selectedFeatures()[0]
            fields = self.layer.fields()
            selected_field = self.field_combo_box.currentText()

            # Set table row count to number of fields + 1 for the Geometry_Type row
            self.table_widget.setRowCount(len(fields) + 1)

            # Add the Geometry_Type field at the top
            geometry_type_item = QTableWidgetItem("Geometry_Type")
            if feature.geometry() and not feature.geometry().isEmpty():
                geometry_value_item = QTableWidgetItem("Has a Geometry")
            else:
                geometry_value_item = QTableWidgetItem("Has No Geometry")
                geometry_value_item.setBackground(QColor("yellow"))  # Highlight in yellow

            self.table_widget.setItem(0, 0, geometry_type_item)
            self.table_widget.setItem(0, 1, geometry_value_item)

            # Populate table with field names and values starting from row 1
            for row, field in enumerate(fields, start=1):
                field_name_item = QTableWidgetItem(field.name())
                value_item = QTableWidgetItem(str(feature[field.name()]))
                self.table_widget.setItem(row, 0, field_name_item)
                self.table_widget.setItem(row, 1, value_item)

                # Only add radio buttons if the second level selection is enabled
                if self.second_level_checkbox.isChecked():
                    # Only add a radio button if the field is not the selected field
                    if field.name() != selected_field:
                        radio_button = QRadioButton()
                        radio_button.setStyleSheet("margin-left:50%; margin-right:50%;")  # Centering the radio button
                        radio_button.toggled.connect(lambda checked, row=row, field_name=field.name(): 
                            self.on_radio_button_toggled(checked, row, field_name))
                        self.radio_button_group.addButton(radio_button)
                        container = QWidget()
                        layout = QHBoxLayout(container)
                        layout.setContentsMargins(0, 0, 0, 0)
                        layout.addWidget(radio_button, 0, Qt.AlignCenter)
                        self.table_widget.setCellWidget(row, 2, container)
                    else:
                        # If it's the selected field, you can set a placeholder or leave it empty
                        self.table_widget.setCellWidget(row, 2, QWidget())  # Empty widget or placeholder

    def on_radio_button_toggled(self, checked, row, field_name):
        """Handle the event when a radio button is toggled."""
        if checked:
            # When the radio button is checked, update the value cell to a combo box with unique values
            self.update_value_cell_to_combo_box(row, field_name)
        else:
            # When the radio button is unchecked, restore the original value
            combo_box = self.table_widget.cellWidget(row, 1)
            if isinstance(combo_box, QComboBox):
                current_value = combo_box.currentText()
                self.restore_original_value(row, current_value)

    def restore_original_value(self, row, value=None):
        """Restore the original value of the cell, changing the combo box back to a normal cell."""
        if value is None:
            # If no value provided, try to get it from the combo box
            combo_box = self.table_widget.cellWidget(row, 1)
            if isinstance(combo_box, QComboBox):
                value = combo_box.currentText()
            else:
                value = ""

        # Remove the combo box and set plain text
        self.table_widget.removeCellWidget(row, 1)
        item = QTableWidgetItem(value)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make it read-only
        self.table_widget.setItem(row, 1, item)

    def update_value_cell_to_combo_box(self, row, field_name):
        """Update the value cell to a combo box and handle selection changes."""
        if self.layer and field_name and self.current_list_field and self.current_list_value:
            # First get features matching the current list selection
            expr = f'"{self.current_list_field}" = \'{self.current_list_value}\''
            request = QgsFeatureRequest().setFilterExpression(expr)
            matching_features = list(self.layer.getFeatures(request))
            
            # Get unique values only from the matching features for the selected field
            unique_values = sorted(set(str(f[field_name]) for f in matching_features if f[field_name] is not None))
            
            combo_box = QComboBox()
            combo_box.addItems(unique_values)
            combo_box.setFixedWidth(120)
            
            # Get the current value from the cell
            current_item = self.table_widget.item(row, 1)
            current_value = current_item.text() if current_item else ""
            
            # Set the current value in the combo box if it exists
            index = combo_box.findText(current_value)
            if index >= 0:
                combo_box.setCurrentIndex(index)
            
            # Connect the combo box selection change to update feature selection
            combo_box.currentTextChanged.connect(
                lambda value, field=field_name: self.on_combo_selection_changed(value, field))
            
            self.table_widget.setCellWidget(row, 1, combo_box)
            if self.previous_combo_row is not None and self.previous_combo_row != row:
                self.restore_original_value(self.previous_combo_row)
            self.previous_combo_row = row

    def on_combo_selection_changed(self, value, field_name):
        """Handle when a value is selected in the combo box."""
        if not value or not self.current_list_value or not self.current_list_field:
            return

        # Build expression that combines both conditions
        expr = f'"{self.current_list_field}" = \'{self.current_list_value}\' AND "{field_name}" = \'{value}\''
        
        # Apply the filter
        self.layer.removeSelection()
        request = QgsFeatureRequest().setFilterExpression(expr)
        features = self.layer.getFeatures(request)
        feature_ids = [f.id() for f in features]
        
        if feature_ids:
            self.layer.selectByIds(feature_ids)
            # Update the table with the selected feature's attributes
            feature = next(self.layer.getFeatures(QgsFeatureRequest().setFilterFids(feature_ids)), None)
            if feature:
                self.populate_table_with_feature(feature)
            if self.interact_checkbox.isChecked():
                self.zoom_to_selected_feature()

    def populate_table_with_feature(self, feature):
        """Populate the table with the feature's attributes while preserving combo boxes."""
        if not feature:
            return
            
        fields = self.layer.fields()
        for row in range(self.table_widget.rowCount()):
            field_name = self.table_widget.item(row, 0).text()
            field_idx = fields.indexOf(field_name)
            if field_idx >= 0:
                value = str(feature[field_idx])
                # Check if the cell has a combo box
                combo_box = self.table_widget.cellWidget(row, 1)
                if isinstance(combo_box, QComboBox):
                    # If it's a combo box, update its value
                    index = combo_box.findText(value)
                    if index >= 0:
                        combo_box.setCurrentIndex(index)
                else:
                    # If it's not a combo box, update the text
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.table_widget.setItem(row, 1, item)

    def populate_null_values(self):
        """Populate the table with '--' for all values when the unique value is 'NULL'."""
        self.table_widget.clearContents()
        if self.layer:
            fields = self.layer.fields()

            # Set table row count to number of fields + 1 for the Geometry_Type row
            self.table_widget.setRowCount(len(fields) + 1)

            # Add the Geometry_Type field at the top
            geometry_type_item = QTableWidgetItem("Geometry_Type")
            geometry_value_item = QTableWidgetItem("--")
            self.table_widget.setItem(0, 0, geometry_type_item)
            self.table_widget.setItem(0, 1, geometry_value_item)

            # Populate table with field names and '--' values starting from row 1
            for row, field in enumerate(fields, start=1):
                field_name_item = QTableWidgetItem(field.name())
                value_item = QTableWidgetItem("--")
                self.table_widget.setItem(row, 0, field_name_item)
                self.table_widget.setItem(row, 1, value_item)

                # Center the radio buttons in the "Additional Selection" column
                radio_button = QRadioButton()
                radio_button.setStyleSheet("margin-left:50%; margin-right:50%;")  # Centering the radio button
                radio_button.toggled.connect(lambda checked, row=row, field_name=field.name(): self.on_radio_button_toggled(checked, row, field_name))
                self.radio_button_group.addButton(radio_button)
                container = QWidget()
                layout = QHBoxLayout(container)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(radio_button, 0, Qt.AlignCenter)
                self.table_widget.setCellWidget(row, 2, container)

    def check_interactive_selection(self):
        """Handle the interactive zoom and pan feature."""
        if self.interact_checkbox.isChecked():
            self.zoom_to_selected_feature()

    def update_zoom_label(self, value):
        """Update the zoom label and zoom to the selected features."""
        self.zoom_label.setText(f"Select zoom level: {value}%")
        if self.interact_checkbox.isChecked():
            self.zoom_to_selected_feature()

    def zoom_to_selected_feature(self):
        """Adjust the zoom level based on the slider value and zoom to the selected feature, accounting for CRS."""
        if self.layer and len(self.layer.selectedFeatures()) == 1:
            feature = self.layer.selectedFeatures()[0]
            if feature.geometry() is None or feature.geometry().isEmpty():
                return  # Do nothing if the feature has no geometry

            extent = feature.geometry().boundingBox()
            canvas_crs = iface.mapCanvas().mapSettings().destinationCrs()
            layer_crs = self.layer.crs()
            transform = QgsCoordinateTransform(layer_crs, canvas_crs, QgsProject.instance())
            extent = transform.transformBoundingBox(extent)
            zoom_factor = (100 - self.zoom_slider.value()) / 100.0
            extent = extent.buffered(zoom_factor * max(extent.width(), extent.height()))
            iface.mapCanvas().setExtent(extent)
            iface.mapCanvas().refresh()

    def toggle_two_way_selection(self, state):
        """Toggle two-way selection functionality and clear the search box when enabled."""
        if state == Qt.Checked:
            self.search_box.clear()
            if self.layer and not isinstance(self.layer, QgsRasterLayer):
                self.layer.selectionChanged.connect(self.update_listbox_with_selection)
        else:
            if self.layer and not isinstance(self.layer, QgsRasterLayer):
                try:
                    self.layer.selectionChanged.disconnect(self.update_listbox_with_selection)
                except TypeError:
                    pass

    def update_listbox_with_selection(self):
        """Update the unique values list box when a feature is selected on the map canvas."""
        if self.layer and self.layer.selectedFeatureCount() == 1:
            feature = self.layer.selectedFeatures()[0]
            field_name = self.field_combo_box.currentText()
            if field_name:
                value = str(feature[field_name])
                items = self.unique_values_list.findItems(value, Qt.MatchExactly)
                if items:
                    self.unique_values_list.setCurrentItem(items[0])

    def filter_values(self):
        """Filter the unique values in the list based on the search text."""
        search_text = self.search_box.text().lower()
        for i in range(self.unique_values_list.count()):
            item = self.unique_values_list.item(i)
            item.setHidden(search_text not in item.text().lower())

    def toggle_dynamic_layer_selection(self, state):
        """Enable or disable dynamic layer selection based on the checkbox state."""
        if state == Qt.Checked:
            iface.layerTreeView().currentLayerChanged.connect(self.on_layer_changed)
            self.layer_combo_box.currentIndexChanged.connect(self.on_layer_changed_from_combo)
        else:
            try:
                iface.layerTreeView().currentLayerChanged.disconnect(self.on_layer_changed)
                self.layer_combo_box.currentIndexChanged.disconnect(self.on_layer_changed_from_combo)
            except TypeError:
                pass

    def toggle_additional_selection(self, state):
        """Toggle the visibility of the Additional Selection column and clear all radio buttons."""
        if state == Qt.Checked:
            self.table_widget.setColumnCount(3)
            self.table_widget.setHorizontalHeaderLabels(["Field Name", "Value", "Additional Selection"])
            
            # Restore bold header font
            header_font = QFont()
            header_font.setBold(True)
            for i in range(self.table_widget.columnCount()):
                header_item = QTableWidgetItem(self.table_widget.horizontalHeaderItem(i).text())
                header_item.setFont(header_font)
                self.table_widget.setHorizontalHeaderItem(i, header_item)
            
            # Restore column widths
            self.table_widget.setColumnWidth(1, 120)  # Value column
            self.table_widget.setColumnWidth(2, 200)  # Additional Selection column
            
            # Set resize modes
            self.table_widget.horizontalHeader().setSectionResizeMode(0, self.table_widget.horizontalHeader().ResizeToContents)
            self.table_widget.horizontalHeader().setSectionResizeMode(1, self.table_widget.horizontalHeader().Fixed)
            self.table_widget.horizontalHeader().setSectionResizeMode(2, self.table_widget.horizontalHeader().ResizeToContents)
            
            # Restore radio buttons if there's a selected feature
            if self.layer and len(self.layer.selectedFeatures()) == 1:
                self.populate_table_with_selected_feature()
        else:
            # Clear all radio button selections
            self.radio_button_group.setExclusive(False)
            for button in self.radio_button_group.buttons():
                button.setChecked(False)
            self.radio_button_group.setExclusive(True)
            
            # Hide the column
            self.table_widget.setColumnCount(2)
            self.table_widget.setHorizontalHeaderLabels(["Field Name", "Value"])
            
            # Restore bold header font for remaining columns
            header_font = QFont()
            header_font.setBold(True)
            for i in range(self.table_widget.columnCount()):
                header_item = QTableWidgetItem(self.table_widget.horizontalHeaderItem(i).text())
                header_item.setFont(header_font)
                self.table_widget.setHorizontalHeaderItem(i, header_item)
            
            # Restore column widths and resize modes for remaining columns
            self.table_widget.setColumnWidth(1, 120)
            self.table_widget.horizontalHeader().setSectionResizeMode(0, self.table_widget.horizontalHeader().ResizeToContents)
            self.table_widget.horizontalHeader().setSectionResizeMode(1, self.table_widget.horizontalHeader().Fixed)
            
            # Restore any combo boxes back to original values
            if self.previous_combo_row is not None:
                self.restore_original_value(self.previous_combo_row)
                self.previous_combo_row = None

    def highlight_features(self, current_row):
        """Highlight features in the layer based on the selected unique value."""
        item = self.unique_values_list.item(current_row)
        if item:
            self.current_list_value = item.text()
            self.current_list_field = self.field_combo_box.currentText()
            self.layer.removeSelection()
            expr = f'"{self.current_list_field}" = \'{self.current_list_value}\''
            if self.current_list_value == "NULL":
                self.populate_null_values()
            else:
                features = self.layer.getFeatures(QgsFeatureRequest().setFilterExpression(expr))
                first_feature = next(features, None)
                if first_feature:
                    self.layer.selectByIds([first_feature.id()])
                    if self.interact_checkbox.isChecked():
                        self.zoom_to_selected_feature()

    def copy_table_data_to_clipboard(self):
        """Copy the content of the table to the clipboard."""
        clipboard = QApplication.clipboard()
        table_data = []

        for row in range(self.table_widget.rowCount()):
            row_data = []
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                if item is not None:
                    row_data.append(item.text())
                else:
                    row_data.append("")
            table_data.append("\t".join(row_data))

        clipboard_text = "\n".join(table_data)
        clipboard.setText(clipboard_text)

    def cancel(self):
        """Triggered when Cancel button is clicked."""
        # Emit signal to close plugin and uncheck toggle
        self.closingPlugin.emit()  

    def closeEvent(self, event):
        # Override close event to hide dialog instead of deleting it
        event.ignore()
        self.hide()
        self.closingPlugin.emit()  # Emit the signal to notify that the dialog is closed