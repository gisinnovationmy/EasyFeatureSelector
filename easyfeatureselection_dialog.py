# -*- coding: utf-8 -*-

import os

from qgis.PyQt import uic, QtWidgets
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QListWidget, QLineEdit, QCheckBox, QPushButton, QSlider, QWidget, QTableWidget, QTableWidgetItem, QApplication 
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QClipboard
from qgis.core import QgsProject, QgsMapLayer, QgsRasterLayer, QgsCoordinateTransform, QgsField, QgsFeature, QgsCoordinateReferenceSystem
from qgis.gui import QgsCollapsibleGroupBox, QgsMessageBar
from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'easyfeatureselection_dialog_base.ui'))

class EasyFeatureSelectionDialog(QtWidgets.QDialog, FORM_CLASS):
    _instance = None  # Singleton instance for dialog

    @classmethod
    def show_dialog(cls):
        # Check if there is an open project with layers
        if not QgsProject.instance().mapLayers():
            # Show a notification if no project is open and return immediately
            iface.messageBar().pushMessage(
                "No Project Open",
                "No project is open. Create a new one or open an existing one to start using these tools.",
                level=QgsMessageBar.WARNING,
                duration=3
            )
            return  # Return immediately to prevent the dialog from being shown

        if cls._instance is None:
            cls._instance = EasyFeatureSelectionDialog()

        cls._instance.show()
        cls._instance.raise_()  # Bring the dialog to the front

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        super(EasyFeatureSelectionDialog, self).__init__(iface.mainWindow())
        self.setupUi(self)

        # Initialize layer and connections
        self.layer = None

        iface.layerTreeView().currentLayerChanged.connect(self.on_layer_changed)
        self.on_layer_changed(iface.activeLayer())

        self.field_combo_box.currentIndexChanged.connect(self.update_unique_values)
        self.unique_values_list.currentRowChanged.connect(self.highlight_features)
        self.search_box.textChanged.connect(self.filter_values)
        self.interact_checkbox.stateChanged.connect(self.check_interactive_selection)
        self.zoom_slider.valueChanged.connect(self.update_zoom_label)
        self.two_way_selection_checkbox.stateChanged.connect(self.toggle_two_way_selection)
        self.copy_button.clicked.connect(self.copy_table_data_to_clipboard)
        self.close_button.clicked.connect(self.close)

        # Make the dialog visually appealing
        self.setWindowModality(Qt.NonModal)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(Qt.Window | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)

        # GroupBox states
        self.field_group_box.setChecked(True)
        self.values_group_box.setChecked(True)
        self.search_group_box.setChecked(True)
        self.table_group_box.setChecked(True)
    
        # Set table background to gray and grid lines in gray
        self.table_widget.setStyleSheet("QTableWidget { background-color: lightgray; gridline-color: gray; }")

        # Set button sizes
        self.copy_button.setFixedSize(200, 30)
        self.close_button.setFixedSize(100, 30)

        # QGIS-style message bar
        self.message_bar = QgsMessageBar()
        self.left_layout.addWidget(self.message_bar)

        # Set header font to bold
        header_font = QFont()
        header_font.setBold(True)
        self.table_widget.horizontalHeaderItem(0).setFont(header_font)
        self.table_widget.horizontalHeaderItem(1).setFont(header_font)

    def connect_signals(self):
        """Connects signals to methods after all methods are defined."""
        if self.layer and not isinstance(self.layer, QgsRasterLayer):
            try:
                self.layer.selectionChanged.connect(self.populate_table_with_selected_feature)
            except AttributeError:
                self.raster_warning_label.show()  # Show warning if the layer is a raster
        else:
            self.raster_warning_label.show()  # Show warning if the layer is a raster

    def disconnect_signals(self):
        """Disconnect signals from the previous layer."""
        if self.layer and not isinstance(self.layer, QgsRasterLayer):
            try:
                self.layer.selectionChanged.connect(self.populate_table_with_selected_feature)
            except AttributeError:
                self.raster_warning_label.show()  # Show warning if the layer is a raster
        else:
            self.raster_warning_label.show()  # Show warning if the layer is a raster

    def on_layer_changed(self, layer):
        """Handle the event when the active layer changes."""
        self.disconnect_signals()  # Disconnect signals from the previous layer
        self.layer = layer
        self.update_layer(layer)
        self.connect_signals()  # Connect signals to the new layer

    def update_layer(self, layer):
        """Update the active layer and UI components."""
        self.layer = layer
        if isinstance(self.layer, QgsRasterLayer):
            self.raster_warning_label.show()  # Show the warning for raster layers
            self.field_combo_box.clear()
            self.unique_values_list.clear()
        elif self.layer and self.layer.type() == QgsMapLayer.VectorLayer:
            self.raster_warning_label.hide()
            self.update_field_names()
            self.update_unique_values()  # Update the unique values listbox on startup
        else:
            self.raster_warning_label.show()
            self.field_combo_box.clear()
            self.unique_values_list.clear()


    def update_field_names(self):
        """Update the field names in the combo box."""
        if self.layer:
            self.field_combo_box.clear()
            self.field_combo_box.addItems([field.name() for field in self.layer.fields()])
            if self.field_combo_box.count() == 0:
                self.clear_table()

    def update_unique_values(self):
        """Update the list of unique values based on the selected field."""
        self.unique_values_list.clear()
        field_name = self.field_combo_box.currentText()
        if self.layer and field_name:
            unique_values = set(str(f[field_name]) for f in self.layer.getFeatures() if f[field_name] is not None)
            self.unique_values_list.addItems(unique_values)
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

    def highlight_features(self, current_row):
        """Highlight features in the layer based on the selected unique value."""
        item = self.unique_values_list.item(current_row)
        if item:
            value = item.text()
            self.layer.removeSelection()
            expr = f'"{self.field_combo_box.currentText()}" = \'{value}\''
            self.layer.selectByExpression(expr)
            if self.interact_checkbox.isChecked():
                self.zoom_to_selected_feature()

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

        # Emit signal to uncheck toggle after generating points
        self.closingPlugin.emit()

    def cancel(self):
        """Triggered when Cancel button is clicked."""
        # Emit signal to close plugin and uncheck toggle
        self.closingPlugin.emit()  

    def closeEvent(self, event):
        # Override close event to hide dialog instead of deleting it
        event.ignore()
        self.hide()
        self.closingPlugin.emit()  # Emit the signal to notify that the dialog is closed