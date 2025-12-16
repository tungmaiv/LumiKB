/**
 * Table component for displaying system configuration settings.
 */

import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ConfigSetting } from "@/types/config";

interface ConfigSettingsTableProps {
  configs: Record<string, ConfigSetting>;
  onEdit: (key: string) => void;
}

export function ConfigSettingsTable({ configs, onEdit }: ConfigSettingsTableProps) {
  // Group configs by category
  const groupedConfigs: Record<string, ConfigSetting[]> = {};

  Object.values(configs).forEach((config) => {
    if (!groupedConfigs[config.category]) {
      groupedConfigs[config.category] = [];
    }
    groupedConfigs[config.category].push(config);
  });

  return (
    <div className="space-y-6">
      {Object.entries(groupedConfigs).map(([category, settings]) => (
        <div key={category}>
          <h3 className="text-lg font-semibold mb-3">{category}</h3>
          <div className="rounded-lg border bg-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Setting</TableHead>
                  <TableHead>Value</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Restart Required</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {settings.map((setting) => (
                  <TableRow key={setting.key}>
                    <TableCell className="font-medium">{setting.name}</TableCell>
                    <TableCell>
                      {typeof setting.value === "boolean"
                        ? setting.value
                          ? "Enabled"
                          : "Disabled"
                        : setting.value}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {setting.description}
                    </TableCell>
                    <TableCell>
                      {setting.requires_restart ? (
                        <span className="text-amber-600 font-medium">Yes</span>
                      ) : (
                        <span className="text-muted-foreground">No</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onEdit(setting.key)}
                      >
                        Edit
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      ))}
    </div>
  );
}
